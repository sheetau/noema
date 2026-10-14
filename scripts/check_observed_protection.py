"""Reject inconsistent observations without confusing a proposal with its truth."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content, FunctionValue
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_assessed_payments import description
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts import check_community_protection as prior
from scripts import check_public_deliberation as deliberation
from scripts.compose_limits import call as k
from scripts.compose_observed_protection import ROOT, PARENT, BUILDERS, OBSERVATION, THREAT_OBSERVATION, OBSERVED_LINK, THREAT_OBSERVED_LINK, POLICY, SOURCE

REPORT = ROOT / 'reports/observed-protection-v1.json'
DOMAIN, SCENES = prior.DOMAIN, prior.SCENES
EXTRA = prior.EXTRA + 'r jorecords[d] h[a] c.r joobservations[a d] h[a] c.'
REFS = dict(prior.REFS, context='k jvcontext[]', observed='c[p jorecords][k jvcontext[]]',
    records='p jorecords', observations='p joobservations')


def expression(name, fields): return k(name, *(REFS[n] for n, _ in fields))


def setup(text, kind):
    calls = {'individual': [('rkz', OBSERVATION), ('rk2', THREAT_OBSERVATION), ('rk3', THREAT_OBSERVED_LINK),
        ('rk4', OBSERVED_LINK), ('rk6', THREAT_OBSERVED_LINK), ('rkw', prior.THREAT_LINK), ('rkx', prior.LINK)],
        'policy': [('rky', prior.SETTINGS), ('rk5', POLICY)],
        'source': [('hzej', prior.SOURCE), ('hzek', SOURCE)]}[kind]
    queries = []
    for name, fields in calls:
        expr = expression(name, fields)
        if name not in ('rkz', 'rk2'): expr = 't[' + expr + '][k jvcontext[]]'
        queries.append('q[' + expr + '].')
    return candidate(text, EXTRA + ''.join(queries))


def model_for(doc, actual=(True, False, True), observed=(True, False, True), natural=(True, False),
              variant='baseline', alpha=True, beta=True):
    table = prior.PROTECT
    if variant == 'inactive_consistent': actual, observed, natural = (False, False, True), (False, False, True), (False, False)
    if variant == 'threat_present': actual, observed, natural = (True, True, True), (True, True, True), (True, True)
    if variant == 'only_intervened_solution': natural = (False, False)
    if variant == 'wrong_threat': actual = (True, True, True)
    if variant == 'false_activity': actual = (True, False, False)
    if variant == 'impossible_activity': table, actual, observed = (False,) * 8, (True, False, False), (True, False, False)
    if variant == 'mixed_outcomes': table = tuple(row[2] for row in prior.ASSIGNMENTS)
    if variant == 'no_solution': table = tuple(not row[2] for row in prior.ASSIGNMENTS)
    model = prior.model_for(doc, table=table, active=actual[0], variant='wrong_worlds' if variant == 'wrong_worlds' else 'baseline')
    oldpolicy, oldactivity, oldthreat = (model[n] for n in ('jvpolicytruth', 'jvactivitytruth', 'jvthreattruth'))
    model['jvpolicytruth'] = lambda point: actual[0] if point == 'actual' else oldpolicy(point)
    model['jvactivitytruth'] = lambda point: actual[2] if point == 'actual' else oldactivity(point)
    model['jvthreattruth'] = lambda point: actual[1] if point == 'actual' else oldthreat(point)
    def equation(variable, state, selected):
        return natural[0] if variable == 'p' else natural[1] if variable == 't' else selected[prior.index(state)] if variable == 's' else False
    model['jveq'] = lambda variable, state: equation(variable, state, table)
    def record(point, bits):
        if point.startswith('w'): bits = tuple(char == '1' for char in point[1:])
        return FunctionValue(('individual',), 'truth', lambda item: bits[prior.VARIABLES.index(item)] if item in prior.VARIABLES else variant == 'dirty_record' and item == 'alpha')
    model['jorecords'] = lambda point: record(point, observed)
    model['jvlaws'] = lambda community: FunctionValue(('individual', prior.STATE_SORT), 'truth', lambda variable, state:
        equation(variable, state, prior.PROTECT if community == 'alpha' else prior.UNCHANGED))
    model['jvactivities'] = lambda community: Content(SCENES, tuple(model['jvactivitytruth'](point) for point in SCENES))
    model['jvthreats'] = lambda community: Content(SCENES, tuple(model['jvthreattruth'](point) for point in SCENES))
    model['joobservations'] = lambda community, point: record(point, observed if (
        community == 'alpha' and alpha or community == 'beta' and beta or community not in ('alpha', 'beta')) else (observed[0], observed[1], not observed[2]))
    return model


def run(doc, **kwargs): return values(doc, model_for(doc, **kwargs), DOMAIN, SCENES)


def individual_checks(texts):
    docs = [setup(t, 'individual') for t in texts]; cases = []
    for bits in product((False, True), repeat=6):
        actual, observed = bits[:3], bits[3:]
        fits = observed == (True, False, True) and actual[0] and actual[2]
        threatfits = fits and not actual[1]
        expected = [fits, threatfits, threatfits, fits, False, actual[0], actual[0]]
        rows = [run(doc, actual=actual, observed=observed) for doc in docs]
        if rows != [expected] * len(docs): raise ValueError('Observation consistency differs: ' + repr((bits, rows, expected)))
        cases.append(dict(actual=list(actual), observed=list(observed), results=expected))
    expected_variants = {
        'inactive_consistent': [True, True, False, False, False, False, False],
        'threat_present': [True] * 7,
        'only_intervened_solution': [False] * 5 + [True, True],
        'wrong_threat': [True, False, False, True, False, True, True],
        'false_activity': [False] * 5 + [True, True],
        'dirty_record': [False] * 5 + [True, True],
        'impossible_activity': [True, True, False, True, False, False, True],
        'mixed_outcomes': [True, True, False, False, False, False, False],
        'no_solution': [False] * 7,
        'wrong_worlds': [True, True, False, False, False, False, False],
    }
    contrasts = {}
    for variant, expected in expected_variants.items():
        rows = [run(doc, variant=variant) for doc in docs]
        if rows != [expected] * len(docs): raise ValueError('Observed protection contrast ' + variant + ': ' + repr(rows))
        contrasts[variant] = expected
    for doc in docs:
        for name in ('jorecords', 'jveq', 'jvpolicytruth', 'jvactivitytruth', 'jvthreattruth'):
            model = model_for(doc); model[name] = guarded(doc)[name]
            try: values(doc, model, DOMAIN, SCENES)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc): raise
            else: raise ValueError('Unknown observation filled in')
    return dict(cases=cases, contrasts=contrasts, observational_fit_does_not_prove_causation=True,
        unknown_relations_refused=True, actual_situation_not_identified_with_counterfactual_world=True)


def community_checks(texts):
    docs = [setup(texts[0], 'policy'), *[setup(t, 'source') for t in texts[1:]]]; cases = []
    for active, alpha, beta in product((False, True), repeat=3):
        expected = [active, active and alpha and beta]
        rows = [run(doc, actual=(active, False, True), observed=(active, False, True), natural=(active, False), alpha=alpha, beta=beta) for doc in docs]
        if rows != [expected] * len(docs): raise ValueError('Community observation borrowed: ' + repr(rows))
        cases.append(dict(active=active, alpha=alpha, beta=beta, results=expected))
    for doc in docs:
        model = model_for(doc); model['joobservations'] = guarded(doc)['joobservations']
        try: values(doc, model, DOMAIN, SCENES)
        except ValueError as exc:
            if 'Unrelated primitive' not in str(exc): raise
        else: raise ValueError('Unknown community observation filled in')
    return dict(cases=cases, own_community_and_point=True, unknown_records_refused=True)


def proposal_checks(texts):
    rows = []
    for text in texts:
        target = expression('hzek', SOURCE)
        extra = EXTRA + deliberation.EXTRA + 'd joalias[] e[' + target + '].'
        base = candidate(text, extra); target_syntax = syntax(description(base, target))
        for alias in (False, True):
            refs = dict(deliberation.REFS, proposal='r[' + ('k joalias[]' if alias else target) + ']')
            query = 't[' + k('hzef', *(refs[n] for n, _ in deliberation.SOURCE)) + '][k jxafter[]]'
            doc = candidate(text, extra + 'q[' + query + '].'); model = deliberation.model_for(doc)
            participation = model['jxparticipates']
            model['jxproposes'] = lambda person, act, desc, point: participation(person, act, point) and desc.syntax == target_syntax
            result = values(doc, model, deliberation.DOMAIN, deliberation.SCENES)
            if result != [not alias]: raise ValueError('Proposing a policy executed its unknown observations')
            rows.append(result)
    return dict(results=rows, unknown_policy_and_observations_not_executed=True, alias_not_substituted=True)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Stored observed protection differs')
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Observed protection roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = dict(characters=len(text), statements=len(doc['statements']))
    doc, parent = parse(texts[1]), parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']: raise ValueError('Parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0013')
    segments = []
    for phrase in ('um diejenigen Gemeinden in Schutz zu nehmen', 'ohne doch diejenigen zu hindern'):
        if unit['text'].count(phrase) != 1: raise ValueError('Ambiguous source range')
        start = unit['text'].index(phrase)
        segments.append(dict(unit=unit['id'], unit_sha256=unit['text_sha256'], status='explicit_interpretive_annotation', range=[start, start + len(phrase)],
            text=phrase, definitions=['rkz', 'rk2', 'rk3', 'rk4', 'rk5', 'rk6', 'hzek']))
    paths = [*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_observed_protection.py', 'scripts/check_observed_protection.py', 'scripts/check_community_protection.py',
        'scripts/check_public_deliberation.py', 'scripts/check_assessed_payments.py', 'scripts/check_conditional_release.py',
        'scripts/check_described_appraisals.py', 'scripts/check_public_assessment.py', 'scripts/check_rod_setup.py',
        'noema/finite_semantics.py', 'noema/extraction.py', 'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_observation_consistent_protection', documents=documents, sizes=sizes,
        individual=individual_checks([texts[0], texts[2]]), communities=community_checks(texts), proposals=proposal_checks(texts[1:]),
        alignment=dict(segments=segments, semantic_completion=False), new_definitions=7, new_primitives=0, new_author_statements=0,
        parent_preserved=True, roundtrips=True, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in paths})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); options = parser.parse_args()
    report = build_report()
    if options.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Observed protection report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream: json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Observed policy, threat, activity and each community record checked against the same model')


if __name__ == '__main__': main()
