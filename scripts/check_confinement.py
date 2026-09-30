"""Compare Noema passage closure against graph search and reject false confinement."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import SequenceValue, evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_caused_conditions import source_unit
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_husbandry_depiction import paragraph_review as previous_review
from scripts.compose_confinement import ROOT, generic_composed, source_composed

REPORT = ROOT / 'reports/confinement-v1.json'
NODES = ('inside', 'threshold', 'outside')
DOMAIN = ('lock', 'being', 'frame', 'guard', 'guards', 'closing', *NODES, 'other')


def sequence(items):
    return SequenceValue(tuple(items), '"individual"')


def values(doc, model, people=DOMAIN, scenes=('now',)):
    return [row['value'] for row in evaluate_document(doc, individuals=people, situations=scenes,
        primitives=model, max_steps=5_000_000, memoize_definitions=True)]


def reachable(nodes, edges, start):
    """Independent iterative graph search; Noema uses intermediate-vertex closure."""
    seen = {start} if start in nodes else set()
    pending = list(seen)
    while pending:
        current = pending.pop()
        for a, b in edges:
            if a == current and b in nodes and b not in seen:
                seen.add(b)
                pending.append(b)
    return seen


def reachability_checks():
    doc = parse(generic_composed()[0] + '''
r za[] j[a].r zb[a a] c.r zc[] a.r zd[] a.
q[c[k rad[k za[] p zb]][k zc[] k zd[]]].
''')
    pairs = tuple((a, b) for a in NODES for b in NODES if a != b)
    accepted = checked = 0
    for bits in product((False, True), repeat=6):
        edges = {pair for pair, enabled in zip(pairs, bits) if enabled}
        for start, end in product(NODES, repeat=2):
            model = {'za': lambda: sequence(NODES), 'zb': lambda a, b: (a, b) in edges,
                     'zc': lambda: start, 'zd': lambda: end}
            actual = values(doc, model, NODES)[0]
            if actual != (end in reachable(NODES, edges, start)):
                raise ValueError('Noema closure differs from graph search')
            checked += 1
            accepted += actual
    return {'graphs': 64, 'endpoint_queries': checked, 'reachable_queries': accepted,
            'oracle': 'independent iterative graph search'}


def generic_candidate():
    return parse(generic_composed()[0] + '''
r za[] j[a].r zb[a] c.r zc[a] c.r zd[a a] c.r ze[a a] c.r zf[] a.
q[k rag[k za[] p zb p zc p zd p ze k zf[]]].
q[k raf[k za[] p zd k zf[] p zc]].
''')


def model_for_graph(nodes, edges, removed, start='inside', inside=('inside',), outside=('outside',)):
    return {'za': lambda: sequence(nodes), 'zb': lambda place: place in inside,
        'zc': lambda place: place in outside, 'zd': lambda a, b: (a, b) in edges,
        'ze': lambda a, b: (a, b) in removed, 'zf': lambda: start}


def deletion_checks():
    doc = generic_candidate()
    # Three forward passages, including the direct bypass, each absent/open/blocked.
    pairs = (('inside', 'threshold'), ('threshold', 'outside'), ('inside', 'outside'))
    rows = []
    for states in product(range(3), repeat=3):
        edges = {edge for edge, state in zip(pairs, states) if state}
        removed = {edge for edge, state in zip(pairs, states) if state == 2}
        before = 'outside' in reachable(NODES, edges, 'inside')
        after = 'outside' in reachable(NODES, edges-removed, 'inside')
        actual = values(doc, model_for_graph(NODES, edges, removed), NODES)
        if actual != [before and not after, before]:
            raise ValueError('Inside, escape and barrier effect were conflated')
        rows.append({'passages': list(states), 'escape_without_restriction': before,
                     'escape_with_restriction': after, 'confined': actual[0]})
    return rows


def boundary_checks():
    doc = generic_candidate()
    edges = {('inside', 'threshold'), ('threshold', 'outside')}
    removed = {('threshold', 'outside')}
    rows = {}
    variants = {
        'baseline': (NODES, edges, removed, 'inside', ('inside',), ('outside',)),
        'permuted': (tuple(reversed(NODES)), edges, removed, 'inside', ('inside',), ('outside',)),
        'duplicate': ((*NODES, 'threshold'), edges, removed, 'inside', ('inside',), ('outside',)),
        'bypass': (NODES, edges | {('inside', 'outside')}, removed, 'inside', ('inside',), ('outside',)),
        'preexisting_inability': (NODES, set(), removed, 'inside', ('inside',), ('outside',)),
        'empty_places': ((), edges, removed, 'inside', ('inside',), ('outside',)),
        'missing_start': (NODES[1:], edges, removed, 'inside', ('inside',), ('outside',)),
        'overlapping_regions': (NODES, edges, removed, 'inside', ('inside', 'outside'), ('outside',)),
        'boundary_start': (NODES, edges, removed, 'threshold', ('inside',), ('outside',)),
        'already_outside': (NODES, edges, removed, 'outside', ('inside',), ('outside',)),
        'reverse_edges': (NODES, {(b, a) for a, b in edges}, removed, 'inside', ('inside',), ('outside',)),
        'unlisted_intermediate': (('inside', 'outside'), edges, removed, 'inside', ('inside',), ('outside',)),
        'no_external_place': (NODES, edges, removed, 'inside', ('inside',), ()),
        'unlisted_external_place': (NODES[:2], edges, removed, 'inside', ('inside',), ('outside',)),
    }
    for name, params in variants.items():
        result = values(doc, model_for_graph(*params), NODES)
        if result[0] != (name in ('baseline', 'permuted', 'duplicate')):
            raise ValueError('Confinement scope or boundary differs: ' + name)
        rows[name] = {'confined': result[0], 'escape_without_restriction': result[1]}
    return rows


def source_model(doc, variant='baseline'):
    def forbidden(*args):
        raise ValueError('Enclosure evaluated unrelated content')
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    def edges(restriction, being, carrier, a, b, context):
        return (restriction, being, carrier, context) == ('lock', 'being', 'frame', 'now') and (
            (a, b) in {('inside', 'threshold'), ('threshold', 'outside')} or
            variant == 'bypass' and (a, b) == ('inside', 'outside')) and variant != 'preexisting_inability'
    model.update(za=lambda: 'being', zb=lambda: 'frame', zc=lambda: 'now', db=lambda: 'guards',
        mp=lambda group: sequence(('guard',) if group == 'guards' else ()),
        aa=lambda being: variant != 'nonhuman_actor' and being == 'guard',
        df=lambda actor, act, context: (actor, act, context) == (
            'other' if variant == 'foreign_actor' else 'guard',
            'other' if variant == 'different_act' else 'closing', 'now'),
        dg=lambda act, context: variant != 'no_event' and (act, context) == ('closing', 'now'),
        qt=lambda carrier, context: sequence(NODES if (carrier, context) == ('frame', 'now') else ()),
        qu=lambda carrier, place, context: (carrier, place, context) == ('frame', 'inside', 'now'),
        qv=lambda carrier, place, context: (carrier, place, context) == ('frame', 'outside', 'now'),
        qw=lambda being, context: 'outside' if variant == 'already_outside' else 'inside',
        q7=lambda restriction, being, carrier, context: variant != 'incomplete_scope' and
            (restriction, being, carrier, context) == ('lock', 'being', 'frame', 'now'), qx=edges,
        qy=lambda restriction, being, carrier, a, b, context: variant != 'no_barrier' and
            (restriction, being, carrier, a, b, context) == (
                'other' if variant == 'wrong_barrier' else 'lock',
                'other' if variant == 'different_being' else 'being',
                'other' if variant == 'different_carrier' else 'frame', 'threshold', 'outside',
                'other' if variant == 'different_context' else 'now'),
        qz=lambda act, restriction, being, carrier, context: variant != 'no_application' and
            (act, restriction, being, carrier, context) == ('closing',
                'other' if variant == 'different_applied_barrier' else 'lock', 'being', 'frame', 'now'))
    required = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return {name: callback for name, callback in model.items() if name in required}


def source_checks():
    doc = candidate(source_composed()[0], 'r za[] a.r zb[] a.r zc[] d.q[t[k q2[k za[] k zb[]]][k zc[]]].')
    rows = {}
    for variant in ('baseline', 'bypass', 'preexisting_inability', 'already_outside', 'incomplete_scope',
                    'no_barrier', 'no_application', 'no_event', 'foreign_actor', 'nonhuman_actor', 'different_act',
                    'wrong_barrier', 'different_applied_barrier', 'different_being', 'different_carrier', 'different_context'):
        actual = values(doc, source_model(doc, variant))[0]
        if actual != (variant == 'baseline'):
            raise ValueError('Enclosure event or reference differs: ' + variant)
        rows[variant] = actual
    return rows


def attribution_checks():
    doc = candidate(source_composed()[0], 'q[k q6[]].')
    rows = {}
    for variant in ('baseline', 'reversed', 'wrong_node', 'wrong_context'):
        def forbidden(*args):
            raise ValueError('Enclosure attribution asserted bodily or mental content')
        model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
        model.update(q5=lambda: 'frame', wa=lambda: 'guard', wh=lambda: 'now',
            qa=lambda node, author, target, depiction, context: (node, author, symbol(target), symbol(depiction), context) == (
                'other' if variant == 'wrong_node' else 'frame', 'guard',
                'q4' if variant == 'reversed' else 'q3', 'q3' if variant == 'reversed' else 'q4',
                'other' if variant == 'wrong_context' else 'now'))
        actual = values(doc, model)[0]
        if actual != (variant == 'baseline'):
            raise ValueError('Confinement depiction framing differs: ' + variant)
        rows[variant] = {'framed': actual, 'contents_evaluated': False}
    return rows


def depiction_checks():
    from scripts.check_husbandry_depiction import source_model as husbandry_model
    doc = candidate(source_composed()[0], 'r za[] a.r zb[] d.q[t[k q4[k za[]]][k zb[]]].')
    domain = ('lock', 'person', 'guardone', 'guardtwo', 'guards', 'frame', 'closing', *NODES, 'other')
    rows = {}
    for variant in ('baseline', 'unowned', 'bypass'):
        model = husbandry_model(doc, 'unowned' if variant == 'unowned' else 'baseline')
        enclosure = source_model(doc, 'bypass' if variant == 'bypass' else 'baseline')
        substitutions = {'person': 'being', 'guardone': 'guard', 'actual': 'now'}
        for name in ('qt', 'qu', 'qv', 'qw', 'qx', 'qy', 'qz', 'q7', 'df', 'dg'):
            callback = enclosure[name]
            model[name] = lambda *args, callback=callback: callback(*(substitutions.get(arg, arg) for arg in args))
        model['qs'] = lambda being, context: 'frame'
        actual = values(doc, model, domain, ('early', 'actual'))[0]
        if actual != (variant == 'baseline'):
            raise ValueError('Husbandry and confinement depiction were not bound: ' + variant)
        rows[variant] = actual
    return rows


def alignment():
    unit = source_unit()
    phrase = 'darin sie sie einsperreten'
    if unit['text'].count(phrase) != 1:
        raise ValueError('Pinned relative clause differs')
    start = unit['text'].index(phrase)
    return {'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'start': start, 'end': start+len(phrase),
        'source': phrase, 'definitions': ['rad', 'rag', 'q2', 'q3', 'q4', 'q6'],
        'status': 'explicit_interpretive_annotation', 'full_semantic_equivalence': False,
        'remaining': ['physical and temporal scope of confinement', 'walking-frame structure and purpose',
                      'docility permission courage and evaluative force', 'facsimile review']}


def paragraph_review():
    review = previous_review()
    item = next(row for row in review['current_obligations'] if row['id'] == 'walking_frame')
    item['progress_ja'] = '有限の移動辺と制限による削除を使い、内部にいることと脱出経路が失われることを区別した。同じ制限・対象・装置・行為者への束縛を検査した。'
    item['required_review_ja'] = '歩行器の構造と用途、移動範囲の現実的な完全性、閉じ込めの開始と時間順序、比喩対応全体。'
    return review


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored confinement differs')
        doc = parse(text)
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Confinement roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    prior = parse((ROOT / 'examples/v014/kant-husbandry-depiction.noema').read_text(encoding='utf-8'))
    if prior['statements'] != parse(source_composed()[0])['statements']:
        raise ValueError('Inherited assertions changed')
    files = [*documents, 'data/confinement-basis-v1.json', 'data/kant-confinement-basis-v1.json',
        'data/confinement-reading-review-v1.json', 'examples/v014/kant-husbandry-depiction.noema',
        'data/kant-husbandry-depiction-basis-v1.json', 'scripts/compose_confinement.py',
        'scripts/check_confinement.py', 'noema/discourse.py', 'noema/finite_semantics.py']
    return {'status': 'finite_passage_deletion_model_and_partial_confinement_reading', 'documents': documents,
        'reachability': reachability_checks(), 'deletion': deletion_checks(), 'boundaries': boundary_checks(),
        'source': source_checks(), 'depiction': depiction_checks(), 'attribution': attribution_checks(), 'alignment': alignment(),
        'paragraph_review': paragraph_review(), 'roundtrips': True, 'inherited_statements_unchanged': True,
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Confinement report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('64 graphs / 576 queries, 27 deletions, 14 boundaries, 16 source, 3 depictions and 4 attributions')


if __name__ == '__main__':
    main()
