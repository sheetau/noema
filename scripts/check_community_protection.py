"""Compare protective and non-interfering models with independent finite solutions."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content, FunctionValue, SequenceValue
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_assessed_payments import description
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts import check_public_deliberation as deliberation
from scripts.compose_limits import call as k
from scripts.compose_community_protection import ROOT, PARENT, BUILDERS, STATE, EQUATIONS, GOAL, WORLDS, MODEL, THREAT, LINK, THREAT_LINK, SETTINGS, SOURCE

REPORT = ROOT / 'reports/community-protection-v1.json'
VARIABLES = ('p', 't', 's')
DOMAIN = (*VARIABLES, 'alpha', 'beta')
ASSIGNMENTS = tuple(product((False, True), repeat=3))
SCENES = ('selection', 'actual', *['w' + ''.join(str(int(x)) for x in row) for row in ASSIGNMENTS])
STATE_SORT = {'kind': 'function', 'parameters': ['individual'], 'result': 'truth'}
EXTRA = '''r jvvars[] j[a].r jveq[a h[a] c] c.r jvfactor[] a.r jvthreatfactor[] a.r jvgoal[h[a] c] c.
r jvworld[h[a] c] d.r jvpolicytruth[d] c.r jvactivitytruth[d] c.r jvthreattruth[d] c.
d jvpolicy[] e[b point[k jvpolicytruth[v point]]].
d jvactivity[] e[b point[k jvactivitytruth[v point]]].
d jvthreat[] e[b point[k jvthreattruth[v point]]].
r jvcontext[] d.r jvanchor[] d.r jvreform[a d] c.r jvretained[a d] c.
r jvcatalog[a] j[a].r jvlaws[a] h[a h[a] c] c.r jvfactors[a] a.r jvthreatfactors[a] a.
r jvgoals[a] h[h[a] c] c.r jvworldmaps[a] h[h[a] c] d.r jvactivities[a] e.r jvthreats[a] e.
r jvcommunities[a] c.r jvchangeconditions[a] e.r jvstayconditions[a] e.'''
REFS = dict(variables='k jvvars[]', equations='p jveq', factor='k jvfactor[]', threatfactor='k jvthreatfactor[]',
    goal='p jvgoal', worlds='p jvworld', policy='k jvpolicy[]', activity='k jvactivity[]', threat='k jvthreat[]',
    anchor='k jvanchor[]')
REFS.update({n: 'p jv' + n for n in ('reform', 'retained', 'catalog', 'laws', 'factors', 'threatfactors', 'goals',
    'worldmaps', 'activities', 'threats', 'communities', 'changeconditions', 'stayconditions')})


def expression(name, fields): return k(name, *(REFS[n] for n, _ in fields))


def setup(text, kind):
    calls = {'effect': [('rks', THREAT), ('rkt', MODEL)],
        'link': [('rku', THREAT_LINK), ('rkv', LINK), ('rkw', THREAT_LINK), ('rkx', LINK)],
        'policy': [('rky', SETTINGS)], 'source': [('hzej', SOURCE)]}[kind]
    queries = []
    for name, fields in calls:
        expr = expression(name, fields)
        if name in ('rkw', 'rkx', 'rky', 'hzej'): expr = 't[' + expr + '][k jvcontext[]]'
        queries.append('q[' + expr + '].')
    return candidate(text, EXTRA + ''.join(queries))


def table_from_corners(corners): return tuple(corners[2 * int(p) + int(t)] for p, t, s in ASSIGNMENTS)


PROTECT = table_from_corners((True, False, True, True))
UNCHANGED = table_from_corners((True, True, True, True))
UNPROTECTED = table_from_corners((True, False, True, False))
HARMFUL = table_from_corners((True, True, False, False))


def index(state): return 4 * int(state('p')) + 2 * int(state('t')) + int(state('s'))


def model_for(doc, table=PROTECT, variant='baseline', active=True, protects=True, harmless=True):
    model = guarded(doc)
    variables = () if variant == 'empty_variables' else ('p', 's') if variant == 'missing_threat' else (*VARIABLES, 'p') if variant == 'duplicate_variable' else VARIABLES
    def equation(variable, state, selected):
        return selected[index(state)] if variable == 's' else False
    def world(state): return 'w000' if variant == 'wrong_worlds' else SCENES[index(state) + 2]
    def policy(point): return (point == 'actual' and active) or point.startswith('w') and (point[1] == ('0' if variant == 'opposite_policy' else '1'))
    def activity(point): return point.startswith('w') and point[3] == ('0' if variant == 'wrong_activity' else '1')
    def threat(point): return point.startswith('w') and point[2] == ('0' if variant == 'wrong_threat' else '1')
    def change(community, point): return community == 'alpha' and point == ('actual' if variant == 'late_selection' else 'selection') and variant != 'empty_selection'
    def stay(community, point): return community == 'beta' and point == ('actual' if variant == 'late_selection' else 'selection') and variant != 'empty_selection'
    model.update(jvvars=lambda: SequenceValue(variables, '"individual"'), jveq=lambda variable, state: equation(variable, state, table),
        jvfactor=lambda: 'p', jvthreatfactor=lambda: 'p' if variant == 'same_factors' else 't',
        jvgoal=lambda state: state('s'), jvworld=world,
        jvpolicytruth=policy, jvactivitytruth=activity, jvthreattruth=threat,
        jvcontext=lambda: 'actual', jvanchor=lambda: 'selection', jvreform=change, jvretained=stay,
        jvcatalog=lambda community: SequenceValue(VARIABLES, '"individual"'),
        jvlaws=lambda community: FunctionValue(('individual', STATE_SORT), 'truth', lambda variable, state:
            equation(variable, state, (PROTECT if protects else UNPROTECTED) if community == 'alpha' else (UNCHANGED if harmless else HARMFUL))),
        jvfactors=lambda community: 'p', jvthreatfactors=lambda community: 't',
        jvgoals=lambda community: FunctionValue((STATE_SORT,), 'truth', lambda state: state('s')),
        jvworldmaps=lambda community: FunctionValue((STATE_SORT,), 'situation', world),
        jvactivities=lambda community: Content(SCENES, tuple(activity(p) for p in SCENES)),
        jvthreats=lambda community: Content(SCENES, tuple(threat(p) for p in SCENES)),
        jvcommunities=lambda community: community in (('beta',) if variant == 'not_community' else ('alpha', 'beta')),
        jvchangeconditions=lambda community: Content(SCENES, tuple(change(community, p) for p in SCENES)),
        jvstayconditions=lambda community: Content(SCENES, tuple(stay(community, p) for p in SCENES)))
    return model


def run(doc, **kwargs): return values(doc, model_for(doc, **kwargs), DOMAIN, SCENES)


def oracle(table):
    solutions = {(p, t): [s for s in (False, True) if s == table[4 * int(p) + 2 * int(t) + int(s)]] for p, t in product((False, True), repeat=2)}
    protective = all(solutions.values()) and all(solutions[False, False]) and not any(solutions[False, True]) and all(solutions[True, False]) and all(solutions[True, True])
    off, on = solutions[False, False], solutions[True, False]
    harmless = bool(off and on) and (not any(off) or all(on))
    return [bool(protective), harmless]


def effect_checks(texts):
    docs = [setup(t, 'effect') for t in texts]; digest = hashlib.sha256(); counts = [0, 0]
    for table in product((False, True), repeat=8):
        expected = oracle(table)
        actual = [run(doc, table=table) for doc in docs]
        if actual != [expected] * len(docs): raise ValueError('Protection differs from independent solution sets: ' + repr((table, actual, expected)))
        counts = [a + int(b) for a, b in zip(counts, expected)]
        digest.update(json.dumps([table, expected], separators=(',', ':')).encode())
    contrasts = {}
    for variant, expected in (('empty_variables', [False, False]), ('missing_threat', [False, True]),
                              ('duplicate_variable', [False, False]), ('same_factors', [False, True])):
        actual = [run(doc, variant=variant) for doc in docs]
        if actual != [expected] * len(docs): raise ValueError('Intervention scope ' + variant + ': ' + repr(actual))
        contrasts[variant] = expected
    return dict(equation_tables=256, assignments_per_table=8, positive_counts=counts, results_sha256=digest.hexdigest(),
        contrasts=contrasts, independent_solution_enumeration=True)


def link_checks(texts):
    docs = [setup(t, 'link') for t in texts]; contrasts = {}
    for variant in ('baseline', 'wrong_worlds', 'opposite_policy', 'wrong_activity', 'wrong_threat', 'same_factors'):
        expected = [True] * 4 if variant == 'baseline' else [False, True, False, True] if variant in ('wrong_threat', 'same_factors') else [False] * 4
        actual = [run(doc, variant=variant) for doc in docs]
        if actual != [expected] * len(docs): raise ValueError('Policy/goal mapping ' + variant + ': ' + repr(actual))
        contrasts[variant] = expected
    for doc in docs:
        if run(doc, active=False) != [True, True, False, False]: raise ValueError('Model effect implied actual policy')
        for name in ('jveq', 'jvworld', 'jvpolicytruth', 'jvactivitytruth', 'jvthreattruth'):
            model = model_for(doc); model[name] = guarded(doc)[name]
            try: values(doc, model, DOMAIN, SCENES)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc): raise
            else: raise ValueError('Unknown intervention filled in')
    return dict(contrasts=contrasts, inactive_policy=[True, True, False, False], unknown_relations_refused=True)


def policy_checks(texts):
    docs = [setup(texts[0], 'policy'), *[setup(t, 'source') for t in texts[1:]]]; cases = []
    for active, protects, harmless in product((False, True), repeat=3):
        expected = [active and protects and harmless]
        actual = [run(doc, active=active, protects=protects, harmless=harmless) for doc in docs]
        if actual != [expected] * len(docs): raise ValueError('Community obligations mixed: ' + repr(actual))
        cases.append(dict(active=active, protects=protects, harmless=harmless, results=expected))
    contrasts = {}
    for variant in ('wrong_worlds', 'opposite_policy', 'wrong_activity', 'wrong_threat', 'empty_selection', 'late_selection', 'not_community'):
        expected = [True] if variant in ('empty_selection', 'late_selection', 'not_community') else [False]
        # Excluding alpha is tested with a failing alpha model; beta still must be safe.
        actual = [run(doc, variant=variant, protects=variant != 'not_community') for doc in docs[1:]]
        if actual != [expected] * (len(docs) - 1): raise ValueError('Source community selection ' + variant + ': ' + repr(actual))
        contrasts[variant] = expected
    return dict(cases=cases, contrasts=contrasts, fixed_selection_anchor=True, independent_positive_selections=True)


def proposal_checks(texts):
    results = []
    for text in texts:
        target = expression('hzej', SOURCE)
        extra = EXTRA + deliberation.EXTRA + 'd jvproposalalias[] e[' + target + '].'
        base = candidate(text, extra)
        target_syntax = syntax(description(base, target))
        for alias in (False, True):
            refs = dict(deliberation.REFS, proposal='r[' + ('k jvproposalalias[]' if alias else target) + ']')
            query = 't[' + k('hzef', *(refs[n] for n, _ in deliberation.SOURCE)) + '][k jxafter[]]'
            doc = candidate(text, extra + 'q[' + query + '].')
            model = deliberation.model_for(doc)
            participates = model['jxparticipates']
            model['jxproposes'] = lambda person, act, desc, point: participates(person, act, point) and desc.syntax == target_syntax
            actual = values(doc, model, deliberation.DOMAIN, deliberation.SCENES)
            if actual != [not alias]: raise ValueError('Protective proposal content was executed or replaced')
            results.append(actual)
    return dict(quoted_policy_can_be_proposed=True, unknown_policy_contents_not_executed=True, alias_not_substituted=True, results=results)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Stored community protection differs')
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Community protection roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = dict(characters=len(text), statements=len(doc['statements']))
    doc, parent = parse(texts[1]), parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']: raise ValueError('Parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0013')
    segments = []
    for phrase in ('um diejenigen Gemeinden in Schutz zu nehmen', 'ohne doch diejenigen zu hindern'):
        if unit['text'].count(phrase) != 1: raise ValueError('Ambiguous source range')
        start = unit['text'].index(phrase)
        segments.append(dict(unit=unit['id'], unit_sha256=unit['text_sha256'], status='explicit_interpretive_annotation', range=[start, start + len(phrase)],
            text=phrase, definitions=['rks', 'rkt', 'rku', 'rkv', 'rkw', 'rkx', 'rky', 'hzej']))
    paths = [*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_community_protection.py', 'scripts/check_community_protection.py', 'scripts/check_public_deliberation.py',
        'scripts/check_assessed_payments.py', 'scripts/check_conditional_release.py', 'scripts/check_described_appraisals.py',
        'scripts/check_public_assessment.py', 'scripts/check_rod_setup.py', 'noema/finite_semantics.py', 'noema/extraction.py',
        'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_model_relative_community_protection', documents=documents, sizes=sizes,
        effects=effect_checks([texts[0], texts[2]]), linkage=link_checks([texts[0], texts[2]]),
        policy=policy_checks(texts), proposals=proposal_checks(texts[1:]),
        alignment=dict(segments=segments, semantic_completion=False), new_definitions=8, new_primitives=0, new_author_statements=0,
        parent_preserved=True, roundtrips=True, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in paths})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); options = parser.parse_args()
    report = build_report()
    if options.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Community protection report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream: json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Protective intervention, non-interference, community scope and the proposed content checked')


if __name__ == '__main__': main()
