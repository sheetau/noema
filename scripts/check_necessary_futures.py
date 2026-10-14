"""Check conditional necessity, branch-local futures and unexecuted modal goals."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from noema.specialization import specialize_definition
from scripts.check_assessed_payments import description
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts import check_blocked_revision as blocked
from scripts import check_successive_cohorts as cohorts
from scripts.compose_limits import call as k
from scripts.compose_necessary_futures import ROOT, PARENT, MODAL_PARENT, MODAL_BASIS, BUILDERS, SOURCE

REPORT = ROOT / 'reports/necessary-futures-v1.json'
EXTRA = '''r jmodalcontext[] d.r jmodalcandidates[d d] c.r jmodalpremise[d] c.r jmodaltruth[d] c.
r jmodalcontinuations[d d d] c.r jmodalepoch[] a.r jmodalperiods[a d] c.
d jmodalcondition[] e[b branch[k jmodalpremise[v branch]]].
d jmodalsubject[] e[b point[k jmodaltruth[v point]]].'''
REFS = blocked.REFS | dict(later='k jmodalepoch[]', periods='p jmodalperiods', condition='k jmodalcondition[]',
    candidates='p jmodalcandidates', continuations='p jmodalcontinuations')
BRANCHES = ('left', 'right')
POINTS = ('endleft', 'endright', 'open')
# This fixture needs four contents and two methods; aliases are covered by the
# earlier epistemic-revision checks, not by extra inert domain inhabitants here.
DOMAIN = ('p', 'q', 'notp', 'notq', 'holder', 'other', 'plan', 'backup', 'later')
SCENES = (*blocked.revision.WORLDS, 'gain', 'clean', 'now', *BRANCHES, *POINTS)


def generic_setup(text, future=False):
    subjects = ('k rjn[k jmodalsubject[] k jmodalcontext[] p jmodalcontinuations]',
                'k rjo[k jmodalsubject[] k jmodalcontext[] p jmodalcontinuations]') if future else ('k jmodalsubject[]',)
    queries = ''.join('q[' + k(name, *([] if name == 'rjl' else [subject]), 'k jmodalcondition[]', 'k jmodalcontext[]', 'p jmodalcandidates') + '].'
        for subject in subjects for name in ('rjk', 'rjl', 'rjm'))
    return candidate(text, EXTRA + queries)


def generic_checks(texts):
    docs = [generic_setup(t) for t in texts]; cases = []
    for bits in product((False, True), repeat=7):
        left, right, ca, cb, a, b, current = bits
        nonempty = left or right
        applicable = left and ca or right and cb
        conditional = nonempty and (not (left and ca) or a) and (not (right and cb) or b)
        want = [conditional, applicable, conditional and applicable]
        for doc in docs:
            model = guarded(doc)
            model.update(jmodalcontext=lambda: 'now',
                jmodalcandidates=lambda c, s: c == 'now' and (s == 'left' and left or s == 'right' and right),
                jmodalpremise=lambda s: s == 'left' and ca or s == 'right' and cb,
                jmodaltruth=lambda s: s == 'left' and a or s == 'right' and b or s == 'now' and current)
            if values(doc, model, ('person',), ('now', *BRANCHES)) != want: raise ValueError('Conditional necessity conflated with current truth or applicability')
        cases.append(dict(bits=list(bits), results=want))
    future_docs = [generic_setup(t, True) for t in texts]; contrasts = {}
    variants = {
        'different_witnesses': ({'left': {'endleft'}, 'right': {'endright'}}, {'endleft', 'endright'}, [True] * 6),
        'one_failure': ({'left': {'endleft'}, 'right': {'endright'}}, {'endleft'}, [False, True, False] * 2),
        'mixed_branch': ({'left': {'endleft', 'open'}, 'right': {'endright'}}, {'endleft', 'endright'}, [True, True, True, False, True, False]),
        'missing_branch': ({'left': {'endleft'}, 'right': set()}, {'endleft'}, [False, True, False] * 2),
        'wrong_context': ({'left': {'endleft'}, 'right': {'endright'}}, {'endleft', 'endright'}, [False, True, False] * 2),
    }
    for variant, (ends, success, want) in variants.items():
        for doc in future_docs:
            model = guarded(doc)
            model.update(jmodalcontext=lambda: 'now', jmodalcandidates=lambda c, s: c == 'now' and s in BRANCHES,
                jmodalpremise=lambda s: s in BRANCHES, jmodaltruth=lambda s: s in success,
                jmodalcontinuations=lambda c, b, s: c == ('other' if variant == 'wrong_context' else 'now') and s in ends.get(b, set()))
            if values(doc, model, ('person',), ('now', *BRANCHES, *POINTS)) != want: raise ValueError('Branch future contrast ' + variant)
        contrasts[variant] = want
    for doc in docs:
        trial = deepcopy(doc); trial['statements'] = trial['statements'][1:2]
        model = guarded(trial)
        model.update(jmodalcontext=lambda: 'now', jmodalcandidates=lambda c, s: c == 'now' and s == 'left',
            jmodalpremise=lambda s: s == 'left')
        if values(trial, model, ('person',), ('now', *BRANCHES)) != [True]:
            raise ValueError('Applicability required knowledge of the consequent')
    return dict(cases=cases, future_contrasts=contrasts, standalone_agrees=True, applicability_does_not_evaluate_consequent=True,
        current_truth_not_required=True, conditional_vacuity_separate_from_applicability=True,
        each_branch_can_have_its_own_witness=True)


def source_setup(text):
    queries = ''.join('q[t[' + k(name, *(REFS[n] for n, _ in SOURCE)) + '][k jmodalcontext[]]].' for name in ('hzdh', 'hzdi', 'hzdj'))
    return candidate(text, blocked.EXTRA + EXTRA + queries)


def source_model(doc, bits=(True,) * 6, variant='baseline'):
    left, right, ca, cb, a, b = bits
    closed = blocked.source_model(doc, gain=False, decrease=False)
    opened = blocked.source_model(doc, gain=True, decrease=True)
    model = guarded(doc)
    for name in ('jkholder', 'jkassessment', 'jkscope', 'jktruth', 'jkcomparisons'):
        model[name] = opened[name]
    starts = (*POINTS, 'now')
    stage = lambda s: 'before' if s in starts else s
    model['jkcorpus'] = lambda actor, claim, s: opened['jkcorpus'](actor, claim, stage(s))
    model['jksupported'] = lambda actor, claim, s: opened['jksupported'](actor, claim, stage(s))
    # 'now' is blocked in all cases. Future openness must not be replaced by it.
    unavailable = {'endleft': a, 'endright': b, 'open': False, 'now': True}
    model['jlavailable'] = lambda actor, plan, s: s in starts and opened['jlavailable'](actor, plan, stage(s))
    def outcomes(actor, plan, s, end):
        if s not in starts: return False
        chosen = closed if unavailable[s] else opened
        return chosen['jloutcomes'](actor, plan, 'before', 'before' if end == s else end)
    model['jloutcomes'] = outcomes
    selected = () if variant == 'empty_candidates' else tuple(s for s, yes in zip(BRANCHES, (left, right)) if yes)
    ends = {'left': {'endleft'}, 'right': {'endright'}}
    if variant == 'mixed_branch': ends['left'].add('open')
    if variant == 'missing_branch': ends['right'] = set()
    if variant == 'only_current': ends = {'left': {'now'}, 'right': {'now'}}
    model.update(jmodalcontext=lambda: 'now', jmodalepoch=lambda: 'later',
        jmodalcandidates=lambda c, s: c == ('other' if variant == 'wrong_context' else 'now') and s in selected,
        jmodalpremise=lambda s: variant != 'no_applicable' and (s == 'left' and ca or s == 'right' and cb),
        jmodalcontinuations=lambda c, branch, point: c == 'now' and point in ends.get('other' if variant == 'wrong_branch' else branch, set()),
        jmodalperiods=lambda epoch, point: epoch == ('other' if variant == 'wrong_epoch' else 'later') and point in (*POINTS, 'now'),
        ic=lambda start, end, context: variant != 'not_future' and (start, context) == ('now', 'now') and end in POINTS)
    return model


def source_checks(texts):
    docs = [source_setup(t) for t in texts]; cases = []
    for bits in product((False, True), repeat=6):
        left, right, ca, cb, a, b = bits
        applicable = left and ca or right and cb
        conditional = (left or right) and (not (left and ca) or a) and (not (right and cb) or b)
        want = [conditional and applicable] * 2 + [conditional]
        rows = [values(d, source_model(d, bits), DOMAIN, SCENES) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Necessary future revision differs: ' + repr((bits, rows, want)))
        cases.append(dict(bits=list(bits), results=want))
    contrasts = {}
    for variant in ('mixed_branch', 'missing_branch', 'only_current', 'empty_candidates', 'wrong_context', 'no_applicable', 'wrong_branch', 'wrong_epoch', 'not_future'):
        want = [True, False, True] if variant == 'mixed_branch' else [False, False, True] if variant == 'no_applicable' else [False] * 3
        rows = [values(d, source_model(d, variant=variant), DOMAIN, SCENES) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Necessary future contrast ' + variant + ': ' + repr(rows))
        contrasts[variant] = want
    for d in docs:
        for name in ('jmodalcandidates', 'jmodalpremise', 'jmodalcontinuations', 'jmodalperiods', 'ic', 'jlavailable', 'jloutcomes'):
            model = source_model(d); model[name] = guarded(d)[name]
            try: values(d, model, DOMAIN, SCENES)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc): raise
            else: raise ValueError('Unknown modal or opportunity relation filled in')
    return dict(cases=cases, contrasts=contrasts, standalone_agrees=True, unknown_relations_refused=True,
        actual_inability_does_not_substitute_future_inability=True)


def purpose_setup(text, constructor):
    doc, old_goal, _, _ = cohorts.source_setup(text)
    statements, doc['statements'] = doc['statements'], []
    doc = parse(format_graph(doc, 'compact') + EXTRA)
    doc['statements'] = statements
    refs = REFS | dict(holder='k jnextgroup[]', later='k jlate[]', periods='p jperiods')
    effect = description(doc, k(constructor, *(refs[n] for n, _ in SOURCE)))
    specialized = specialize_definition(doc, 'hzcq', 'jmodalcause', {1: effect}); doc = specialized.document
    goal = description(doc, k('jmodalcause', 'i[person a][k jg[v person k je[]]]', 'p jlcause'))
    def replace(x):
        if isinstance(x, list): return [replace(y) for y in x]
        if not isinstance(x, dict): return x
        if x == old_goal: return deepcopy(goal)
        return {n: replace(y) for n, y in x.items()}
    doc['statements'] = replace(doc['statements'])
    trace = dict(bound_positions=specialized.bound_positions, disquotations_removed=specialized.disquotations_removed,
        expanded_definitions=specialized.expanded_definitions)
    return parse(format_graph(doc, 'compact')), goal, effect, trace


def purpose_checks(texts):
    result = {}
    for constructor in ('hzdh', 'hzdi', 'hzdj'):
        setups = [purpose_setup(t, constructor) for t in texts]
        for s in setups:
            for aimed in (False, True):
                if values(s[0], cohorts.source_model(s, aimed=aimed), cohorts.DOMAIN, cohorts.SCENES) != [True, aimed]:
                    raise ValueError('Modal causal purpose executed or ignored its intention')
            for notation in ('compact', 'full'):
                form = format_graph(s[0], notation)
                if parse(form) != s[0] or parse(decode(encode(form, 'v2'))) != s[0]: raise ValueError('Modal causal purpose roundtrip differs')
        result[constructor] = dict(unknown_modality_and_achievement_not_executed=True,
            specialization=[s[3] for s in setups], standalone_agrees=True, closed_roundtrips=True)
    return result


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Stored necessary future differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Necessary future roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = dict(characters=len(text), statements=len(doc['statements']))
    doc, parent = parse(texts[1]), parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']: raise ValueError('Parent changed')
    shared = next(d for d in parse((ROOT / MODAL_PARENT).read_text(encoding='utf-8'))['declarations'] if d['name'] == 's5k')
    if next(d for d in doc['declarations'] if d['name'] == 's5k') != shared: raise ValueError('Shared scientific necessity changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0013')
    phrase = 'unmöglich werden muß'
    if unit['text'].count(phrase) != 1: raise ValueError('Ambiguous source phrase')
    start = unit['text'].index(phrase)
    segment = dict(unit=unit['id'], unit_sha256=unit['text_sha256'], status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase, definitions=['s5k', 'rjk', 'rjl', 'rjm', 'rjn', 'rjo', 'hzdh', 'hzdi', 'hzdj'])
    paths = [*documents, PARENT, MODAL_PARENT, MODAL_BASIS, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_necessary_futures.py', 'scripts/check_necessary_futures.py', 'scripts/check_successive_cohorts.py',
        'scripts/check_blocked_revision.py', 'scripts/check_assessed_payments.py', 'scripts/check_conditional_release.py',
        'scripts/check_described_appraisals.py', 'scripts/check_rod_setup.py', 'noema/finite_semantics.py',
        'noema/extraction.py', 'noema/specialization.py', 'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_conditional_necessary_future_interpretation', documents=documents, sizes=sizes,
        generic=generic_checks([texts[0], texts[2]]), source=source_checks(texts[1:]), purposes=purpose_checks(texts[1:]),
        alignment=dict(segments=[segment], semantic_completion=False), added_definitions=9, new_definitions=8,
        reused_definitions=['s5k'], shared_definition_unchanged=True, new_primitives=0, new_author_statements=0,
        parent_preserved=True, roundtrips=True, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in paths})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); options = parser.parse_args()
    report = build_report()
    if options.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Necessary future report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream: json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Shared modal definition, nonvacuous conditionals and branch-local necessary futures checked')


if __name__ == '__main__': main()
