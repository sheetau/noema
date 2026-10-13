"""Check identity-sensitive membership, transported paths and non-cancelling flow."""
import argparse
from fractions import Fraction as F
import hashlib
from itertools import product
import json

from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue
from noema.first_order_proofs import verify
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_light_complex import evaluate_numbers
from scripts.check_plane_waveforms import setup, evaluate, OPS
from scripts.check_real_products import MEANINGS, assertion
from scripts.check_moving_light_trip import literal
from scripts.check_rod_setup import guarded
from scripts.compose_limits import call as k, app, op, both, v
from scripts.compose_transported_contents import ROOT, PARENT, BUILDERS, CUT, POINT, generic_composed

REPORT = ROOT / 'reports/transported-contents-v1.json'


def membership_base():
    doc = extract_document(parse(generic_composed()[0]), roots=['sefa', 'sefb'], statement_indices=[]).document
    return format_graph(doc, 'compact') + 'r ja[a] c.r jb[a a] c.r jc[a] c.r jd[] a.r je[] a.'


def membership_checks():
    pair = k('sefa', 'p ja', 'p jb', k('jd'), k('je'))
    persistent = k('sefb', 'p ja', 'p jb', 'p jc', k('jd'))
    doc = parse(membership_base() + 'q[' + pair + '].q[' + persistent + '].')
    domain = ('first', 'second', 'start', 'middle', 'end', 'outside')
    pairs = tuple(product(domain[:2], domain[2:5]))
    totals = [0, 0]
    def run(edges, scope, period):
        model = {'ja': lambda item: item in scope, 'jb': lambda item, time: (item, time) in edges,
                 'jc': lambda time: time in period, 'jd': lambda: 'start', 'je': lambda: 'end'}
        return values(doc, model, domain)
    for bits in product((False, True), repeat=6):
        edges = {p for p, present in zip(pairs, bits) if present}
        expected = [all(((item, 'start') in edges) == ((item, 'end') in edges) for item in domain[:2]),
                    all(((item, 'start') in edges) == ((item, time) in edges)
                        for item, time in product(domain[:2], domain[2:5]))]
        actual = run(edges, domain[:2], domain[2:5])
        if actual != expected:
            raise ValueError('Persistent membership differs from independent sets')
        totals = [total + value for total, value in zip(totals, actual)]
    cases = {
        'exit_and_reenter': ({('first', 'start'), ('first', 'end')}, domain[:2], domain[2:5], [True, False]),
        'equal_count_replacement': ({('first', 'start'), ('second', 'end')}, domain[:2], domain[2:5], [False, False]),
        'empty_period': (set(), domain[:2], (), [True, False]),
        'reference_outside_period': (set(), domain[:2], ('middle', 'end'), [True, False]),
        'outside_label_ignored': ({('outside', 'middle')}, domain[:2], domain[2:5], [True, True]),
        'middle_omitted': ({('first', 'start'), ('first', 'end')}, domain[:2], ('start', 'end'), [True, True]),
        'empty_object_scope': ({('first', 'middle')}, (), domain[2:5], [True, True]),
    }
    contrasts = {}
    for name, (edges, scope, period, expected) in cases.items():
        actual = run(edges, scope, period)
        if actual != expected:
            raise ValueError('Membership contrast failed: ' + name)
        contrasts[name] = actual
    end_in = k('jc', k('je'))
    reverse = k('sefb', 'p ja', 'p jb', 'p jc', k('je'))
    claims = {
        'persistence_has_a_reference_in_period': op('y', persistent, k('jc', k('jd'))),
        'persistence_implies_endpoints_in_period': op('y', both(persistent, end_in), pair),
        'reference_can_shift_inside_period': op('y', both(persistent, end_in), reverse),
        'endpoints_alone_imply_persistence': op('y', pair, persistent),
        'persistence_covers_an_unspecified_time': op('y', persistent, pair),
    }
    proofs = verify(parse(membership_base() + ''.join('s[' + body + '].' for body in claims.values())))
    if [row['status'] for row in proofs] != ['valid'] * 3 + ['invalid'] * 2:
        raise ValueError('Membership quantifier laws differ')
    return {'finite_membership_patterns': 64, 'accepted_endpoint_pairs': totals[0], 'accepted_persistent_sets': totals[1],
            'contrasts': contrasts, 'laws': {name: {'status': row['status'], 'countermodel_found': row['countermodel'] is not None,
                'formula_sha256': hashlib.sha256(row['formula'].encode('utf-8')).hexdigest()}
                for name, row in zip(claims, proofs, strict=True)}}


def polynomial_checks():
    text = generic_composed()[0]
    V, a, b, c, x, y, z, t, delta, density, incoming, outgoing = map(v,
        'light ax ay az ox oy oz time delta density incoming outgoing'.split())
    mul = lambda x, y: k('ad', x, y)
    add = lambda x, y: k('ab', x, y)
    pos = lambda axis, offset, time: k('sefc', V, axis, offset, time)
    coords = [pos(axis, offset, t) for axis, offset in zip((a, b, c), (x, y, z))]
    claims = {
        'transport_preserves_offset_squared_distance': assertion('light ax ay az ox oy oz time',
            op('e', k('sebd', V, a, b, c, *coords, t), k('seaa', x, y, z))),
        'transport_composes_in_time': assertion('light ax ox time delta',
            op('e', pos(a, pos(a, x, t), delta), pos(a, x, add(t, delta)))),
        'advective_current_has_zero_relative_component': assertion('light ax density',
            op('e', k('sefd', mul(density, mul(V, a)), density, mul(V, a)), literal(0))),
        'no_exchange_implies_balanced_totals': assertion('incoming outgoing',
            op('y', k('seff', incoming, outgoing), k('sefe', incoming, outgoing))),
        'balanced_totals_imply_no_exchange_counterexample': assertion('',
            op('y', k('sefe', literal(1), literal(1)), k('seff', literal(1), literal(1)))),
        'fixed_ball_preserves_membership_counterexample': assertion('', op('e',
            k('seaa', k('sefc', literal(1), literal(1), literal(0), literal(2)), literal(0), literal(0)), literal(0))),
    }
    rows = {}
    for name, claim in claims.items():
        result = verify_universal(parse(text + claim), MEANINGS, timeout_ms=20000)[0]
        if result['status'] != ('invalid' if name.endswith('counterexample') else 'valid'):
            raise ValueError('Transport algebra failed: ' + name + repr(result))
        rows[name] = result
    return {'claims': rows, 'rational_algebra_only': True, 'all_real_cut_laws_proved': False,
            'electromagnetic_energy_transport_proved': False}


def geometry_checks(texts):
    names = tuple('j' + n for n in 'abcdefghi')
    args = list(map(k, names))
    query = ''.join('q[' + k(name, *args) + '].' for name in ('segc', 'segd', 'segf'))
    docs = [abstract(candidate(text, ''.join('r ' + n + '[] ' + CUT + '.' for n in names) + query), OPS) for text in texts]
    directions = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (F(3, 5), F(4, 5), 0))
    offsets = ((0, 0, 0), (3, 4, 0), (6, 0, 0))
    rows = []
    for direction, offset, time in product(directions, offsets, (-2, 0, 3)):
        norm = sum(n*n for n in offset)
        expected = [norm <= 25, norm == 25, True]
        actual = [evaluate_numbers(doc, names, (5, *direction, 5, *offset, time)) for doc in docs]
        if any(row != expected for row in actual):
            raise ValueError('Transported point classification differs: ' + repr(actual))
        rows.append({'direction': list(map(str, direction)), 'offset': list(offset), 'time': time, 'results': actual[0]})
    contrasts = {}
    for label, index, value in (('zero_radius', 4, 0), ('negative_radius', 4, -5),
                                ('zero_light', 0, 0), ('negative_light', 0, -5), ('nonunit_direction', 1, 2)):
        numbers = [5, 1, 0, 0, 5, 3, 4, 0, 2]
        numbers[index] = value
        actual = [evaluate_numbers(doc, names, numbers) for doc in docs]
        if actual != [[False]*3]*len(docs):
            raise ValueError('Invalid transport domain accepted: ' + label)
        contrasts[label] = actual[0]
    return {'cases': rows, 'contrasts': contrasts, 'standalone_agrees': True,
            'real_arithmetic_abstracted_to_registered_rational_cuts': True}


def family_checks(texts):
    # Labels are deliberately independent of the three spatial axes.
    extra = 'r ja[a] c.r jb[a] ' + POINT + '.r jc[] a.r jd[] ' + CUT + '.'
    numbers = [k('bb', literal(n)) for n in (5, 1, 0, 0, 5)]
    query = 'q[' + k('segh', 'p ja', 'p jb', *numbers, k('jd'), k('jc')) + '].'
    docs = [abstract(candidate(text, extra + query), OPS) for text in texts]
    domain = ('x', 'y', 'z', 't', 'first', 'second', 'outside')
    rows = {}
    for label, time in product(('first', 'second', 'outside'), (-2, 0, 3)):
        actual = []
        for doc in docs:
            fixture, model = setup(doc)
            sort = next(d['result'] for d in doc['declarations'] if d['name'] == 'jb')
            def origin(item):
                # Nonzero unused time component must not move the spatial origin.
                coords = dict(zip(('x', 'y', 'z', 't'), (0 if item != 'second' else 6, 0, 0, 19)))
                return FunctionValue(tuple(sort['parameters']), sort['result'], lambda axis: fixture.make(coords.get(axis, 0)))
            model.update(ja=lambda item: item in ('first', 'second'), jb=origin, jc=lambda: label, jd=lambda: fixture.make(time))
            used = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
            actual.append(values(doc, {key: value for key, value in model.items() if key in used}, domain))
        if actual != [[label == 'first']]*len(docs):
            raise ValueError('Label or initial-position binding differs')
        rows[label + ':' + str(time)] = actual[0]
    return {'cases': rows, 'standalone_agrees': True, 'origins_time_component_ignored': True}


def flow_checks(texts):
    names = tuple('j' + n for n in 'abcdefgh')
    query = 'q[' + k('segj', *map(k, names)) + '].'
    docs = [abstract(candidate(text, ''.join('r '+n+'[] '+CUT+'.' for n in names) + query), OPS) for text in texts]
    cases = {
        'parallel_flow': ((5, 1, 0, 0, 2, 10, 0, 0), True),
        'oblique_flow': ((5, F(3, 5), F(4, 5), 0, 2, 6, 8, 0), True),
        'zero_density': ((5, 1, 0, 0, 0, 0, 0, 0), True),
        'wrong_direction': ((5, 1, 0, 0, 2, -10, 0, 0), False),
        'unmatched_transverse_flow': ((5, 1, 0, 0, 2, 10, 1, 0), False),
        'negative_density': ((5, 1, 0, 0, -2, -10, 0, 0), False),
        'nonunit_direction': ((5, 2, 0, 0, 2, 20, 0, 0), False),
        'zero_light': ((0, 1, 0, 0, 2, 0, 0, 0), False),
    }
    rows = {}
    for name, (numbers, expected) in cases.items():
        actual = [evaluate_numbers(doc, names, numbers) for doc in docs]
        if actual != [[expected]]*len(docs):
            raise ValueError('Relative flow condition differs: ' + name)
        rows[name] = actual[0]
    return {'cases': rows, 'standalone_agrees': True, 'not_a_boundary_integral_or_continuity_equation': True}


def finite_refusal(text):
    args = [k('bb', literal(n)) for n in (5, 1, 0, 0, 5, 3, 4, 0)]
    doc = abstract(candidate(text, 'q[' + k('segg', *args) + '].'), OPS)
    _, model = setup(doc)
    try:
        evaluate(doc, model)
    except ValueError as exc:
        if 'Cannot finitely quantify' not in str(exc):
            raise
        return {'refused': True, 'reason': str(exc), 'all_times_not_replaced_with_samples': True}
    raise ValueError('Infinite real-time condition was silently sampled')


def alignment():
    source = json.loads((ROOT / 'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit = next(u for u in source['units'] if u['id'] == 'einstein-1905:u0205')
    excerpts = [
        ('keine Energie hindurch', ['segj'], '点ごとの相対流れが零という強い輸送モデル。電磁エネルギーとの物理的接続は未完。'),
        ('diese Fläche dauernd denselben Lichtkomplex umschließt', ['sefb', 'segg', 'segh', 'segi'],
         '固定ラベルの初期位置から作る等速経路と移動球への持続する所属。光の集合の物理的同一性、著者の帰結提示と後続の問いは未完。'),
    ]
    rows = []
    for excerpt, definitions, review in excerpts:
        if unit['text'].count(excerpt) != 1:
            raise ValueError('Transport source range is ambiguous')
        start = unit['text'].index(excerpt)
        rows.append({'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'range': [start, start+len(excerpt)],
            'text': excerpt, 'definitions': definitions, 'status': 'partial', 'review_ja': review})
    return {'segments': rows, 'semantic_completion': False, 'interpretation': 'explicit_parallel_transport_model'}


def build_report():
    documents, sizes, texts = {}, {}, []
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored transported contents differ')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Transport roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
        sizes[stem] = {'characters': len(text), 'statements': len(doc['statements'])}
    source, parent = parse(texts[1]), parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if source['declarations'][:len(parent['declarations'])] != parent['declarations'] or source['statements'] != parent['statements']:
        raise ValueError('Parent changed')
    paths = [*documents, PARENT, *['data/'+stem+'-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_transported_contents.py', 'scripts/check_transported_contents.py',
        'scripts/check_plane_waveforms.py', 'scripts/check_light_complex.py', 'scripts/check_tau_differential.py',
        'scripts/check_comoving_labels.py', 'scripts/check_coordinate_correspondence.py',
        'noema/first_order_proofs.py', 'noema/polynomial_proofs.py', 'noema/finite_semantics.py', 'noema/extraction.py',
        'artifacts/written-units-v1/einstein-1905.json']
    return json.loads(json.dumps({'status': 'partial_parallel_transport_model_not_physical_identity_completion',
        'documents': documents, 'sizes': sizes, 'membership': membership_checks(), 'polynomial': polynomial_checks(),
        'geometry': geometry_checks(texts[1:]), 'family': family_checks(texts[1:]), 'flow': flow_checks(texts[1:]),
        'finite_refusal': finite_refusal(texts[2]), 'alignment': alignment(), 'roundtrips': True, 'parent_preserved': True,
        'new_primitives': 0, 'new_author_statements': 0, 'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Transport report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Identity-sensitive persistence and explicit parallel transport checked')


if __name__ == '__main__':
    main()
