"""Check endpoint-free persistence without treating finite observations as infinity."""
import argparse
import hashlib
from itertools import product
import json

import z3

from noema.finite_semantics import evaluate_document
from noema.first_order_proofs import verify as first_order_verify
from noema.rational_proofs import verify as rational_verify
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.compose_unending_persistence import ROOT, PARENT, generic_composed, source_composed, witnesses_composed

REPORT = ROOT / 'reports/unending-persistence-v1.json'


def values(doc, model, scenes):
    return [row['value'] for row in evaluate_document(doc, individuals=('person', 'method', 'faculty', 'act'),
        situations=scenes, primitives=model, max_steps=2_000_000, memoize_definitions=True, memoize_expressions=True)]


def finite_document():
    return parse(generic_composed()[0] + '''
r za[d] c.r zb[d d] c.r zc[d] c.r zd[] d.
q[k ta[p za p zb]].q[k rca[p za p zb k zd[] p zc]].
q[k rbz[p za p zb k zd[]]].q[k rcb[p za p zb k zd[] p zc]].
''')


def finite_order_checks():
    doc = finite_document()
    counts = {}
    for size in (1, 2, 3):
        scenes = tuple(range(size))
        pairs = tuple(product(scenes, repeat=2))
        valid_orders = 0
        for bits in product((False, True), repeat=len(pairs)):
            edges = {pair for pair, enabled in zip(pairs, bits) if enabled}
            model = {'za': lambda point: True, 'zb': lambda a, b: (a, b) in edges,
                'zc': lambda point: True, 'zd': lambda: 0}
            actual = values(doc, model, scenes)
            # Independent finite relation conditions, without relying on ta.
            strict = all((a, a) not in edges for a in scenes)
            total = all(((a, b) in edges) != ((b, a) in edges) for a in scenes for b in scenes if a != b)
            transitive = all((a, c) in edges for a, b in edges for left, c in edges if b == left)
            ordered = strict and total and transitive
            if actual != [ordered, ordered, False, False]:
                raise ValueError('A finite end or cycle was treated as unending: ' + str((size, edges, actual)))
            valid_orders += ordered
        counts[str(size)] = {'relations': 2 ** len(pairs), 'strict_linear_orders': valid_orders, 'unending_models': 0}
    return counts


def finite_tail_checks():
    doc = finite_document()
    scenes = (0, 1, 2)
    rows = []
    for states in product((False, True), repeat=3):
        for anchor in scenes:
            actual = values(doc, {'za': lambda point: True, 'zb': lambda a, b: a < b,
                'zc': lambda point: states[point], 'zd': lambda: anchor}, scenes)
            expected = all(states[point] for point in scenes if point >= anchor)
            if actual != [True, expected, False, False]:
                raise ValueError('Future-tail persistence forgot a later point or invented an endless history')
            rows.append({'states': states, 'anchor': anchor, 'result': actual})
    for history in ((), (1, 2)):
        actual = values(doc, {'za': lambda point: point in history, 'zb': lambda a, b: a < b,
            'zc': lambda point: True, 'zd': lambda: 0}, scenes)
        if actual[1:] != [False, False, False]:
            raise ValueError('A missing anchor supplied vacuous persistence')
    return {'cases': rows, 'empty_history_and_missing_anchor_refused': True}


def general_laws():
    text = generic_composed()[0] + 'r za[d] c.r zb[d d] c.r zc[d] c.r zd[] d.r ze[] d.'
    args = 'p za p zb k zd[]'
    tail = f'k rby[{args}]'
    persistent = f'k rca[{args} p zc]'
    endless = f'k rcb[{args} p zc]'
    last = 'w[k za[k ze[]]][f point d[y[k za[v point]][u[k zb[k ze[] v point]]]]]'
    start = 'w[k ta[p za p zb]][w[k za[k zd[]]][k zc[k zd[]]]]'
    laws = {
        'persistence_includes_anchor': f'y[{persistent}][k zc[k zd[]]]',
        'unending_entails_persistence': f'y[{endless}][{persistent}]',
        'unending_has_a_strictly_later_point': f'y[{endless}][g later d[w[k za[v later]][k zb[k zd[] v later]]]]',
        'a_last_point_blocks_unending': f'y[{last}][u[k rbz[{args}]]]',
        'advancing_anchor_preserves_future_persistence': f'f later d[y[w[{persistent}][c[{tail}][v later]]][k rca[p za p zb v later p zc]]]',
        'advancing_anchor_preserves_unending': f'f later d[y[w[{endless}][c[{tail}][v later]]][k rcb[p za p zb v later p zc]]]',
        'persistence_implies_unending': f'y[{persistent}][{endless}]',
        'state_at_anchor_implies_persistence': f'y[{start}][{persistent}]',
    }
    doc = parse(text + ''.join(f's[{body}].' for body in laws.values()))
    results = first_order_verify(doc, timeout_ms=10000, max_expansion=500_000)
    if [row['status'] for row in results] != ['valid'] * 6 + ['invalid'] * 2:
        raise ValueError('Unexpected temporal proof result: ' + str([row['status'] for row in results]))
    return {'domain': 'arbitrary nonempty situation sort', 'solver_version': z3.get_version_string(),
        'claims': {name: {'status': row['status'], 'formula_sha256': hashlib.sha256(row['formula'].encode()).hexdigest(),
            'countermodel_found': row['countermodel'] is not None} for name, row in zip(laws, results, strict=True)}}


def numerical_witnesses():
    doc = parse(witnesses_composed()[0])
    results = rational_verify(doc, {'aa': 'less'})
    names = ('bounded_interval_has_no_last_point', 'bounded_interval_is_not_unbounded',
        'nonnegative_rationals_have_no_last_point', 'nonnegative_rationals_are_unbounded')
    if any(row['status'] != 'valid' for row in results):
        raise ValueError('Exact rational witness failed')
    return {'solver_version': z3.get_version_string(), 'domain': 'all rational numbers; no finite samples',
        'situations_not_retyped_as_numbers': True,
        'claims': {name: {'status': row['status']} for name, row in zip(names, results, strict=True)}}


def source_checks():
    doc = candidate(source_composed()[0], '''r za[] a.r zb[] d.
q[t[k h26[k za[]]][k zb[]]].q[t[k h2k[k za[]]][k zb[]]].q[t[k h2l[k za[]]][k zb[]]].''')
    scenes = ('past', 'now', 'later')
    rows = {}
    cases = {
        'all_future': (('now', 'later'), ('now', 'later'), scenes, False, [True, True, False]),
        'only_selected_interval': (('now',), ('now',), scenes, False, [True, False, False]),
        'missing_anchor_state': (('now', 'later'), ('later',), scenes, False, [False, False, False]),
        'empty_history': (('now',), scenes, (), False, [False, False, False]),
        'anchor_outside_history': (('now',), scenes, ('past', 'later'), False, [False, False, False]),
        'cyclic_history': (('now', 'later'), scenes, scenes, True, [False, False, False]),
    }
    for name, (scope, immature, history, cyclic, expected) in cases.items():
        model = guarded(doc)
        model.update(za=lambda: 'person', zb=lambda: 'now',
            ia=lambda person, anchor, point: person == 'person' and point in history,
            ib=lambda person, anchor, point: (person, anchor) == ('person', 'now') and point in scope,
            ic=lambda first, second, anchor: scenes.index(first) < scenes.index(second) or (cyclic and first == 'later' and second == 'past'),
            aa=lambda person: person == 'person',
            ae=lambda person, method, start: (person, method) == ('person', 'method') and start not in immature,
            af=lambda person, method, start, end: (person, method) == ('person', 'method') and start == end,
            ap=lambda person, method, start, end: (person, method) == ('person', 'method') and start == end,
            ab=lambda faculty, person, point: (faculty, person) == ('faculty', 'person'),
            ac=lambda person, faculty, act, point: (person, faculty, act) == ('person', 'faculty', 'act'),
            ad=lambda *args: False)
        actual = values(doc, model, scenes)
        if actual != expected:
            raise ValueError('A finite source history confused the three temporal strengths: ' + name)
        rows[name] = actual
    return rows


def horizon_refusal():
    doc = parse(generic_composed()[0] + '''
r za[d] c.r zb[d d] c.r zc[d] c.r zd[] d.r ze[b d] c.
q[k rcc[p za p zb k zd[] p zc p ze]].
''')
    model = {'za': lambda point: True, 'zb': lambda a, b: a < b, 'zc': lambda point: True,
        'zd': lambda: 0, 'ze': lambda horizon, point: horizon < point}
    try:
        values(doc, model, (0, 1))
    except ValueError as error:
        if 'Cannot finitely quantify the rational number domain' not in str(error):
            raise
        return {'refused': True, 'reason': str(error)}
    raise ValueError('A few numeric horizons substituted for all rational thresholds')


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'unending-persistence'), (source_composed, 'kant-unending-persistence'),
            (witnesses_composed, 'rational-tail-witnesses')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored persistence document differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Persistence notation roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    source_text = source_composed()[0]
    source = parse(source_text)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if source['declarations'][:len(parent['declarations'])] != parent['declarations'] or source['statements'] != parent['statements']:
        raise ValueError('Earlier Kant content changed')
    paths = list(documents) + [PARENT, 'data/unending-persistence-basis-v1.json', 'data/kant-unending-persistence-basis-v1.json',
        'data/rational-tail-witnesses-basis-v1.json', 'scripts/compose_unending_persistence.py', 'scripts/check_unending_persistence.py',
        'noema/discourse.py', 'noema/finite_semantics.py', 'noema/first_order_proofs.py', 'noema/rational_proofs.py']
    report = {'status': 'distinguished_temporal_strengths_not_new_source_translation', 'documents': documents,
        'finite_orders': finite_order_checks(), 'finite_tails': finite_tail_checks(), 'general_laws': general_laws(),
        'numerical_witnesses': numerical_witnesses(), 'source_cases': source_checks(), 'horizon_refusal': horizon_refusal(),
        'roundtrips': True, 'parent_preserved': True,
        'alignment': {'segments': [], 'new_source_ranges': False, 'unending_individual_life_not_attributed_to_kant': True},
        'notation_size': {'canonical_source_document_characters': len(source_text), 'added_characters': len(source_text) - len((ROOT / PARENT).read_text(encoding='utf-8'))},
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}
    return json.loads(json.dumps(report, ensure_ascii=False))


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Unending persistence report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Future-tail, endpoint-free and numerically unbounded persistence checked')


if __name__ == '__main__':
    main()
