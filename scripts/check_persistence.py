"""Countermodels for temporal coverage, attitude and source population bindings."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product, permutations
import json

from noema.finite_semantics import Content, SequenceValue, evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import decode, encode
from scripts.compose_persistence import ROOT, generic_composed, source_composed
from scripts.check_described_explanations import symbol

REPORT = ROOT / 'reports/persistence-v1.json'
POINTS = ('early', 'middle', 'late')


def generic_candidate():
    return parse(generic_composed()[0] + '''
r za[d] c.r zb[d] c.r zc[d d] c.r zd[] e.r ze[a i[h[a] e] d] c.r zf[] a.
d zg[person a] e[k zd[]].
q[k ta[p za p zc]].q[k tb[p za p zb p zc]].
q[k tc[p zb k zd[]]].q[k td[k zf[] r[p zg] p zb p ze]].
''')


def generic_values(doc, history=POINTS, scope=POINTS, edges=None, state=POINTS, favor=POINTS):
    if edges is None:
        edges = {(a, b) for i, a in enumerate(POINTS) for b in POINTS[i+1:]}
    model = {'za': lambda s: s in history, 'zb': lambda s: s in scope, 'zc': lambda a, b: (a, b) in edges,
        'zd': lambda: Content(POINTS, tuple(p in state for p in POINTS)),
        'ze': lambda person, description, s: person == 'reader' and symbol(description) == 'zg' and s in favor,
        'zf': lambda: 'reader'}
    return [r['value'] for r in evaluate_document(doc, individuals=('reader', 'other'), situations=POINTS, primitives=model)]


def order_checks():
    doc = generic_candidate()
    pairs = tuple((a, b) for a in POINTS for b in POINTS if a != b)
    total_orders = [{(a, b) for i, a in enumerate(order) for b in order[i+1:]} for order in permutations(POINTS)]
    accepted = 0
    for bits in product((False, True), repeat=len(pairs)):
        edges = {pair for pair, on in zip(pairs, bits) if on}
        actual = generic_values(doc, edges=edges)[0]
        if actual != (edges in total_orders):
            raise ValueError('Strict temporal order differs from permutation ordering')
        accepted += actual
    rows = {}
    for bits in product((False, True), repeat=3):
        scope = tuple(p for p, on in zip(POINTS, bits) if on)
        expected = bool(scope) and all(p in scope for p in POINTS[POINTS.index(scope[0]):POINTS.index(scope[-1])+1])
        actual = generic_values(doc, scope=scope)[1]
        if actual != expected:
            raise ValueError('Temporal interval membership differs')
        rows[''.join(str(int(b)) for b in bits)] = actual
    if generic_values(doc, history=(), scope=())[0:2] != [False, False]:
        raise ValueError('Empty history accepted')
    if generic_values(doc, history=POINTS[:2], scope=POINTS)[1]:
        raise ValueError('Scope outside history accepted')
    edges = total_orders[0] | {('middle', 'middle')}
    if generic_values(doc, edges=edges)[0]:
        raise ValueError('Reflexive chronology accepted')
    return {'relations_checked': 64, 'strict_total_orders': accepted, 'intervals': rows,
        'empty_history_rejected': True, 'outside_history_rejected': True, 'reflexive_order_rejected': True}


def state_attitude_checks():
    doc = generic_candidate()
    rows = []
    for state_bits, favor_bits in product(product((False, True), repeat=3), repeat=2):
        state = tuple(p for p, on in zip(POINTS, state_bits) if on)
        favor = tuple(p for p, on in zip(POINTS, favor_bits) if on)
        actual = generic_values(doc, state=state, favor=favor)
        if actual != [True, True, all(state_bits), all(favor_bits)]:
            raise ValueError('Persistent state was confused with its positive attitude')
        rows.append({'state': list(state_bits), 'favor': list(favor_bits), 'persistent': actual[2], 'favored_throughout': actual[3]})
    empty = generic_values(doc, scope=())
    if empty[2:] != [False, False]:
        raise ValueError('Empty time scope accepted vacuously')
    return {'cases': rows, 'empty_scope_rejected': True}


def source_candidate(quantify=False):
    doc = parse(source_composed()[0])
    doc['statements'] = []
    text = format_graph(doc, 'compact') + '\nr za[] j[a].r zb[] b.r zc[] d.\n'
    text += 'q[t[k if[k za[]]][k zc[]]].' if quantify else 'q[k ig[k za[] k zb[] k zc[]]].'
    return parse(text)


def source_value(doc, variant='baseline'):
    people = ('alice', 'bob', 'cara')
    domain = people + ('plan', 'faculty', 'act')
    scenes = ('text', *POINTS, 'other')
    immature = {(person, point) for person in people for point in POINTS}
    favorable = {(person, point) for person in people[:2] for point in POINTS}
    if variant == 'middle_state_change':
        immature.remove(('bob', 'middle'))
    if variant == 'middle_attitude_change':
        favorable.remove(('alice', 'middle'))
    if variant == 'different_people_have_state_and_attitude':
        immature = {('alice', point) for point in POINTS}
        favorable = {('bob', point) for point in POINTS}
    calls = []
    def attitude(person, description, point):
        name = symbol(description)
        calls.append((person, name, point))
        return name == ('bs' if variant == 'wrong_attitude_target' else 'bf') and (person, point) in favorable
    model = {d['name']: (lambda *args: False) for d in doc['declarations'] if d['kind'] == 'primitive'}
    model.update({
        'aa': lambda p: p in people and not (p == 'cara' and variant == 'nonhuman_population'),
        'ab': lambda organ, person, scene: organ == 'faculty' and person in people,
        'ac': lambda person, organ, act, scene: person in people and organ == 'faculty' and act == 'act',
        'ae': lambda person, plan, scene: person in people and plan == 'plan' and (person, scene) not in immature,
        'af': lambda person, plan, start, end: person in people and plan == 'plan' and start == end,
        'ap': lambda person, plan, start, end: person in people and plan == 'plan' and start == end,
        'ha': lambda a, b: a+b, 'hb': lambda a, b: a*b, 'hc': lambda a, b: a<b, 'hd': lambda value: Fraction(int(value)),
        'hr': lambda pop, context: variant != 'incomplete_population' and pop.items == people and context == 'text',
        'hs': lambda ratio, context: context == 'text' and ratio >= Fraction(3, 5),
        'ia': lambda person, context, point: person in people and context == ('other' if variant == 'wrong_context' else 'text') and point in POINTS,
        'ib': lambda person, context, point: person in people and context == 'text' and point in POINTS
              and variant != 'empty_life_scope' and not (variant == 'missing_middle_scope' and point == 'middle'),
        'ic': lambda left, right, context: context == 'text' and left in POINTS and right in POINTS and
              ((left, right) in {('early', 'middle'), ('middle', 'late'), ('late', 'early')} if variant == 'cyclic_time' else POINTS.index(left) < POINTS.index(right)),
        'id': attitude, 'za': lambda: SequenceValue(people, '"individual"'),
        'zb': lambda: Fraction(1, 3) if variant == 'wrong_ratio' else Fraction(2, 3), 'zc': lambda: 'text'})
    result = evaluate_document(doc, individuals=domain, situations=scenes, primitives=model, max_steps=20000000)
    return result[0]['value'], sorted({name for _, name, _ in calls})


def source_checks():
    doc = source_candidate()
    variants = ('baseline', 'middle_state_change', 'middle_attitude_change', 'different_people_have_state_and_attitude',
        'wrong_attitude_target', 'nonhuman_population', 'incomplete_population', 'wrong_context',
        'empty_life_scope', 'missing_middle_scope', 'cyclic_time', 'wrong_ratio')
    rows = {}
    for variant in variants:
        value, targets = source_value(doc, variant)
        if value != (variant == 'baseline') or targets != ['bf']:
            raise ValueError('Source temporal population binding differs: ' + variant)
        rows[variant] = value
    try:
        source_value(source_candidate(quantify=True))
    except ValueError as error:
        if 'rational number domain' not in str(error):
            raise
        refusal = str(error)
    else:
        raise ValueError('Unbounded ratio quantification was silently approximated')
    return {'cases': rows, 'attitude_target': 'bf', 'unbounded_ratio_refusal': refusal}


def source_alignment():
    units = json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units']
    unit = next(u for u in units if u['id'] == 'kant-1784:u0009')
    digest = hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()
    if digest != unit['text_sha256'] or digest != 'c719db3057e3bfe00e0791532aa4a79b4126930dca80e2042e55cf4150f1dd2b':
        raise ValueError('Kant source changed')
    fragments = []
    for phrase, names in (('ein so großer Theil der Menschen', ['if', 'hq']), ('gerne Zeitlebens unmündig bleiben', ['ie', 'bf'])):
        if unit['text'].count(phrase) != 1:
            raise ValueError('Source fragment missing or ambiguous')
        start = unit['text'].index(phrase)
        fragments.append({'start': start, 'end': start+len(phrase), 'source': phrase, 'definitions': names})
    return {'unit': unit['id'], 'unit_sha256': digest, 'fragments': fragments,
        'status': 'quantifier_and_temporal_property_connected_partial_clause',
        'lifetime_scope_and_granularity_are_interpretive_assumptions': True,
        'positive_attitude_implies_free_choice': False,
        'remaining': ['causes', 'prior natural release', 'concession nevertheless', 'guardians clause', 'rest of paragraph', 'facsimile review']}


def quotation_check():
    doc = parse(source_composed()[0])
    doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + '\nq[k uc[k wb[] k wa[] r[k if[l[a][]]] k wh[]]].')
    def forbidden(*args):
        raise ValueError('A described temporal assertion evaluated its content')
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    seen = []
    def attributed(node, author, description, scene):
        syntax = json.loads(description.syntax)
        seen.append(syntax)
        return node == 'fragment' and author == 'author' and scene == 'text' and syntax['symbol'] == 'if'
    model.update(wb=lambda: 'fragment', wa=lambda: 'author', wh=lambda: 'text', uc=attributed)
    result = evaluate_document(doc, individuals=('fragment', 'author'), situations=('text',), primitives=model)
    if result != [{'kind': 'ask', 'value': True}] or len(seen) != 1:
        raise ValueError('Temporal assertion quotation differs')
    return {'description_symbol': 'if', 'content_evaluated': False,
        'note': 'An empty population is quoted as a diagnostic only; no source population is asserted.'}


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored persistence document differs')
        doc = parse(text)
        for notation in ('compact', 'full'):
            canonical = format_graph(doc, notation)
            if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
                raise ValueError('Persistence roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    files = [*documents, 'data/persistence-basis-v1.json', 'data/kant-lifelong-state-basis-v1.json',
        'examples/v014/kant-large-share.noema', 'data/kant-large-share-basis-v1.json',
        'scripts/compose_persistence.py', 'scripts/check_persistence.py', 'noema/discourse.py', 'noema/finite_semantics.py']
    return {'status': 'ordered_persistence_partial_source_connection', 'documents': documents,
        'order_checks': order_checks(), 'state_attitude_checks': state_attitude_checks(), 'source_checks': source_checks(),
        'source_alignment': source_alignment(), 'quotation_check': quotation_check(), 'roundtrips': True,
        'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Persistence report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('64 time relations, 8 scopes, 64 state/attitude combinations and 12 source bindings checked')


if __name__ == '__main__':
    main()
