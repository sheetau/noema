"""Verify class inclusion, shared agency and author attribution independently."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import SequenceValue, evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import decode, encode
from scripts.check_described_appraisals import candidate, source_model as appraisal_model
from scripts.check_described_explanations import symbol
from scripts.compose_scoped_groups import ROOT, generic_composed, source_composed

REPORT = ROOT / 'reports/scoped-groups-v1.json'
PEOPLE = ('person', 'other', 'third', 'guardone', 'guardtwo', 'population', 'guards',
          'appointment', 'appointmenttwo', 'activity', 'activitytwo', 'low', 'high')
SCENES = ('actual', 'belief', 'alternative', 'loss', 'prior')


def values(doc, model, people=PEOPLE, scenes=SCENES, memoize=True):
    return [r['value'] for r in evaluate_document(doc, individuals=people, situations=scenes,
        primitives=model, max_steps=5_000_000, memoize_definitions=memoize)]


def inclusion_checks():
    doc = parse(generic_composed()[0] + '''
r za[a] c.r zb[a] c.r zc[a] c.q[k ro[p za p zb p zc]].
''')
    rows = []
    people = ('first', 'second')
    for bits in product((False, True), repeat=6):
        population, included, selected = [set(p for p, bit in zip(people, bits[i:i+2]) if bit)
                                          for i in (0, 2, 4)]
        model = {'za': lambda p: p in population, 'zb': lambda p: p in included, 'zc': lambda p: p in selected}
        result = values(doc, model, people, ('context',))
        expected = bool(included) and included <= population and included <= selected
        if result != [expected]:
            raise ValueError('Entire included class was replaced with an overlap')
        rows.append({'population': sorted(population), 'included': sorted(included),
                     'selected': sorted(selected), 'valid': result[0]})
    return rows


def coverage_checks():
    doc = parse(generic_composed()[0] + '''
r za[a] c.r zb[a] c.r zc[a a] c.q[k rp[p za p zb p zc]].
''')
    actors, targets = ('a', 'b'), ('x', 'y')
    rows = []
    for bits in product((False, True), repeat=4):
        edges = {pair for pair, bit in zip(product(actors, targets), bits) if bit}
        model = {'za': lambda p: p in actors, 'zb': lambda p: p in targets, 'zc': lambda a, b: (a, b) in edges}
        result = values(doc, model, actors+targets, ('context',))
        expected = all(any((a, t) in edges for t in targets) for a in actors) and all(
            any((a, t) in edges for a in actors) for t in targets)
        if result != [expected]:
            raise ValueError('Collective coverage differs')
        rows.append({'edges': [list(edge) for edge in sorted(edges)], 'valid': result[0], 'all_pairs': len(edges) == 4})
    empty = {}
    for name, active_actors, active_targets in (
        ('no_actors', (), targets), ('no_targets', actors, ()), ('both_empty', (), ())):
        model = {'za': lambda p: p in active_actors, 'zb': lambda p: p in active_targets, 'zc': lambda *args: True}
        result = values(doc, model, actors+targets, ('context',))
        if result != [False]:
            raise ValueError('Empty collective coverage accepted')
        empty[name] = result[0]
    return {'cases': rows, 'empty_scopes': empty}


def agency_checks():
    doc = parse(generic_composed()[0] + '''
r za[a] c.r zb[] d.r zc[a d] c.r zd[a a d] c.q[k rr[p za k zb[] p zc p zd]].
''')
    actors, acts = ('a', 'b'), ('one', 'two')
    rows = []
    for bits in product((False, True), repeat=6):
        occurs = {act for act, bit in zip(acts, bits[:2]) if bit}
        edges = {pair for pair, bit in zip(product(actors, acts), bits[2:]) if bit}
        model = {'za': lambda p: p in actors, 'zb': lambda: 'context',
            'zc': lambda act, context: act in occurs and context == 'context',
            'zd': lambda actor, act, context: (actor, act) in edges and context == 'context'}
        result = values(doc, model, actors+acts, ('context',))
        expected = any(all((actor, act) in edges for actor in actors) for act in occurs)
        if result != [expected]:
            raise ValueError('Separate activities were conflated with shared participation')
        rows.append({'occurs': sorted(occurs), 'participation': [list(edge) for edge in sorted(edges)], 'shared_activity': result[0]})
    return rows


def source_model(doc, variant='baseline'):
    selected = {'person', 'other', 'third'}
    if variant == 'female_not_judging':
        selected.remove('person')
    model = appraisal_model(doc, actual_risk=variant == 'actual_danger', judged_people=selected)
    def members(group):
        population = ('person', 'other', 'third')
        guards = ('guardone', 'guardtwo')
        if variant == 'empty_guards':
            guards = ()
        elif variant == 'duplicate_guard':
            guards += ('guardone',)
        return SequenceValue(population if group == 'population' else guards if group == 'guards' else (), '"individual"')
    assigned = {('guardone', 'person'), ('guardone', 'other'), ('guardtwo', 'third')}
    if variant == 'uncovered_target':
        assigned.remove(('guardtwo', 'third'))
    if variant == 'irrelevant_guard':
        assigned = {('guardone', person) for person in ('person', 'other', 'third')}
    def assumed(act, actor, target, point):
        return (actor, target) in assigned and act == 'appointment' and point == (
            'actual' if variant == 'not_prior' else 'prior')
    def explanation(factor, description, effect, result, context):
        return variant != 'no_causal_adoption' and (factor, symbol(description), effect, symbol(result), context) == (
            'guards', 'dk' if variant == 'wrong_factor' else 'dl',
            'guards' if variant == 'wrong_effect_subject' else 'population',
            'uw' if variant == 'danger_instead_of_judgment' else 'dn', 'actual')
    def forbidden(*args):
        raise ValueError('Class inclusion executed aesthetic judgments or presumed spontaneous initiative')
    model.update(mv=lambda: 'population', db=lambda: 'guards', mp=members,
        za=lambda: 'guardone', zb=lambda: 'person', zc=lambda: 'actual',
        aa=lambda person: person in ('person', 'other', 'third', 'guardone', 'guardtwo')
            and not (variant == 'nonhuman_guard' and person == 'guardtwo'),
        da=lambda person, context: context == 'actual' and person == (
            'guardone' if variant == 'female_outside_population' else 'person') and variant != 'empty_female_class',
        dc=lambda actor, target, context: variant != 'no_current_role' and (actor, target) in assigned and context == 'actual',
        dd=lambda before, after: (before, after) == ('prior', 'actual'),
        de=lambda actor, act, point: actor in ('guardone', 'guardtwo') and act == (
            'appointmenttwo' if variant == 'wrong_assumption_act' else 'appointment') and point == 'prior',
        ob=assumed, dv=lambda *args: variant != 'claimed_only' and assumed(*args),
        df=lambda actor, act, context: actor in ('guardone', 'guardtwo') and context == 'actual' and act == (
            'activitytwo' if variant == 'separate_activities' and actor == 'guardtwo' else 'activity'),
        dg=lambda act, context: variant != 'no_activity' and act in ('activity', 'activitytwo') and context == 'actual',
        ea=explanation, dt=forbidden, oa=forbidden,
        u4=lambda ratio, context: ratio >= Fraction(3, 5) and context == 'actual')
    required = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return {name: value for name, value in model.items() if name in required}


def source_checks():
    doc = candidate(source_composed()[0], '''
r za[] a.r zb[] a.r zc[] d.
q[t[k di[k za[] k zb[]]][k zc[]]].q[t[k dk[k db[]]][k zc[]]].
q[t[k dl[k db[]]][k zc[]]].q[t[k dn[k mv[]]][k zc[]]].q[t[k dp[]][k zc[]]].
q[t[k uw[k zb[]]][k zc[]]].
''')
    expected = {
        'baseline': [True, True, True, True, True, False],
        'actual_danger': [True, True, True, True, True, True],
        'female_not_judging': [True, True, True, False, False, False],
        'female_outside_population': [True, True, True, False, False, False],
        'empty_female_class': [True, True, True, False, False, False],
        'empty_guards': [True, False, False, True, False, False],
        'duplicate_guard': [True, False, False, True, False, False],
        'uncovered_target': [True, False, True, True, False, False],
        'irrelevant_guard': [True, False, True, True, False, False],
        'nonhuman_guard': [True, False, False, True, False, False],
        'no_current_role': [False, False, True, True, False, False],
        'not_prior': [False, False, True, True, False, False],
        'wrong_assumption_act': [False, False, True, True, False, False],
        'claimed_only': [False, False, True, True, False, False],
        'separate_activities': [True, True, False, True, False, False],
        'no_activity': [True, True, False, True, False, False],
        'no_causal_adoption': [True, True, True, True, False, False],
        'wrong_factor': [True, True, True, True, False, False],
        'wrong_effect_subject': [True, True, True, True, False, False],
        'danger_instead_of_judgment': [True, True, True, True, False, False],
    }
    rows = {}
    for name, target in expected.items():
        result = values(doc, source_model(doc, name))
        if result != target:
            raise ValueError('Scoped group source differs: ' + name + ' ' + repr(result))
        rows[name] = dict(zip(('individual_role', 'collective_role', 'shared_activity',
                               'included_class_and_large_share', 'causal_claim_content', 'actual_danger'), result))
    return rows


def attribution_checks():
    from scripts.check_kant_discourse import base_model, DOMAIN, NODES
    doc = parse(source_composed()[0])
    domain = (*DOMAIN, 'explanation', 'illustration', 'payment', 'convenience', 'guardians', 'other')
    rows = {}
    for variant in ('baseline', 'wrong_node', 'wrong_author', 'wrong_claim', 'wrong_context',
                    'reversed_order', 'wrong_referent', 'wrong_label'):
        model = base_model(doc)
        def forbidden(*args):
            raise ValueError('Attribution endorsed gender classification, beauty, danger or causal content')
        for name in ('da', 'dc', 'de', 'df', 'dg', 'dt', 'ea', 'u2', 'uq', 'ur', 'us'):
            model[name] = forbidden
        def claim(node, author, description, context):
            if node in ('conclusion', 'explanation', 'convenience'):
                return True
            return (node, author, json.loads(description.syntax), context) == (
                'other' if variant == 'wrong_node' else 'guardians',
                'other' if variant == 'wrong_author' else 'author',
                {'kind': 'call', 'symbol': 'un' if variant == 'wrong_claim' else 'dp', 'arguments': []},
                'other' if variant == 'wrong_context' else 'text')
        def before(a, b, context):
            edges = [('conclusion', 'explanation'), ('explanation', 'illustration'), ('illustration', 'payment'),
                ('explanation', 'convenience'), ('convenience', 'illustration'),
                ('guardians', 'payment') if variant == 'reversed_order' else ('payment', 'guardians')]
            return context == 'text' and ((a in NODES and b in NODES and NODES.index(a) < NODES.index(b)) or (a, b) in edges)
        def label(node, author, referent, depiction, context):
            return (node, author, symbol(referent), symbol(depiction), context) == ('guardians', 'author',
                'ds' if variant == 'wrong_referent' else 'dr',
                'dr' if variant == 'wrong_label' else 'ds', 'text')
        model.update(mw=lambda: 'explanation', s3=lambda: 'illustration', t4=lambda: 'payment',
            uo=lambda: 'convenience', dq=lambda: 'guardians', ua=lambda *args: True, ub=lambda *args: True,
            uc=claim, ud=lambda *args: True, uf=lambda *args: True, qa=lambda *args: True,
            s4=lambda *args: True, s5=lambda *args: True, ue=before, du=label)
        result = values(doc, model, domain, ('text',))
        expected = [True]*6 + [variant not in ('wrong_node', 'wrong_author', 'wrong_claim', 'wrong_context', 'reversed_order'),
                              variant not in ('wrong_referent', 'wrong_label')]
        if result != expected:
            raise ValueError('Author attribution or conventional label differs: ' + variant + repr(result))
        rows[variant] = {'statements': result, 'underlying_contents_evaluated': False}
    return rows


def alignment():
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units']
                if u['id'] == 'kant-1784:u0009')
    text = unit['text']
    digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
    if digest != 'c719db3057e3bfe00e0791532aa4a79b4126930dca80e2042e55cf4150f1dd2b':
        raise ValueError('Pinned source differs')
    starts = [text.index(s) for s in ('Daß der bei weitem', '(darunter', 'den Schritt', ': dafür', 'Nachdem')]
    references = (['u5', 'dn'], ['ro', 'dr', 'ds', 'rq'], ['up', 'uw', 'ux', 'uy', 'uz'], ['di', 'dk', 'dl', 'do', 'dp'])
    segments = []
    for start, stop, names in zip(starts, starts[1:], references):
        excerpt = text[start:stop].rstrip()
        segments.append({'start': start, 'end': start+len(excerpt), 'source': excerpt,
                         'definitions': names, 'status': 'partial_explicit_reading'})
    return {'unit': unit['id'], 'unit_sha256': digest, 'segments': segments,
        'sentence_end': starts[-1], 'full_semantic_equivalence': False,
        'remaining': ['sex classification and aesthetic evaluation basis', 'authority and causal mechanism',
            'gutigst irony and degree', 'schon and auch focus', 'pronoun scope', 'following comparisons', 'facsimile review']}


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored scoped group differs')
        doc = parse(text)
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Scoped group roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    files = [*documents, 'data/scoped-groups-basis-v1.json', 'data/kant-scoped-groups-basis-v1.json',
        'examples/v014/kant-described-appraisals.noema', 'data/kant-described-appraisals-basis-v1.json',
        'data/scoped-groups-reading-review-v1.json', 'scripts/compose_scoped_groups.py', 'scripts/check_scoped_groups.py',
        'noema/discourse.py', 'noema/finite_semantics.py']
    return {'status': 'partial_inclusion_collective_guardians_and_attributed_label', 'documents': documents,
        'inclusion': inclusion_checks(), 'coverage': coverage_checks(), 'agency': agency_checks(),
        'source': source_checks(), 'attribution': attribution_checks(), 'alignment': alignment(),
        'roundtrips': True, 'definitions_replaced_by_primitives': False,
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    result = build_report()
    if args.verify_only:
        if result != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Scoped group report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('64 inclusion, 16 coverage, 64 agency, 20 source and 8 attribution cases verified')


if __name__ == '__main__':
    main()
