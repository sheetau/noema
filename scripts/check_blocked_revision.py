"""Check possible outcomes, independent revision goals and caused obstruction."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from noema.specialization import specialize_definition
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts import check_epistemic_revision as revision
from scripts.compose_limits import call as k
from scripts.compose_blocked_revision import ROOT, PARENT, BUILDERS, SOURCE

REPORT = ROOT / 'reports/blocked-revision-v1.json'
GENERIC_EXTRA = '''r jlactor[] a.r jlstart[] d.r jlavailable[a a d] c.
r jloutcomes[a a d d] c.r jltruth[d] c.d jlgoal[] e[b point[k jltruth[v point]]].'''
GENERIC_ARGS = 'k jlactor[] k jlgoal[] k jlstart[] p jlavailable p jloutcomes'
EXTRA = revision.EXTRA + '''r jlstart[] d.r jlavailable[a a d] c.r jloutcomes[a a d d] c.
r jlagents[a] c.r jlcause[a i[e] d] c.r jlaim[a i[e] d] c.'''
REFS = revision.REFS | dict(available='p jlavailable', outcomes='p jloutcomes')
DOMAIN = (*revision.DOMAIN, 'plan', 'backup', 'alpha', 'beta', 'act')
SCENES = (*revision.SCENES, 'gain', 'clean')


def generic_setup(text):
    return candidate(text, GENERIC_EXTRA + 'q[k rja[k jlactor[] k jlstart[] p jlavailable p jloutcomes]].' +
        ''.join('q[k ' + n + '[' + GENERIC_ARGS + ']].' for n in ('xb', 'xc', 'rjb')))


def generic_checks(texts):
    docs = [generic_setup(t) for t in texts]
    subsets = [set(s for i, s in enumerate(('win', 'lose')) if mask & (1 << i)) for mask in range(4)]
    count = 0
    for enabled, first, second, success in product((False, True), subsets, subsets, subsets):
        valid = not enabled or bool(first) and bool(second)
        possible = enabled and bool((first | second) & success)
        guaranteed = enabled and (bool(first) and first <= success or bool(second) and second <= success)
        want = [valid, possible, guaranteed, valid and not possible]
        for doc in docs:
            model = guarded(doc)
            model.update(jlactor=lambda: 'holder', jlstart=lambda: 'start',
                jlavailable=lambda a, p, s: enabled and a == 'holder' and s == 'start' and p in ('plan', 'backup'),
                jloutcomes=lambda a, p, s, e: a == 'holder' and s == 'start' and e in (first if p == 'plan' else second if p == 'backup' else set()),
                jltruth=lambda e: e in success)
            if values(doc, model, ('holder', 'plan', 'backup'), ('start', 'win', 'lose')) != want:
                raise ValueError('Success guarantee confused with possibility or missing outcomes')
        count += 1
    return dict(models=count, methods=2, independent_set_oracle=True, standalone_agrees=True,
        absent_methods_allow_inability=True, empty_results_do_not_prove_inability=True)


def source_setup(text):
    queries = ''.join('q[t[' + k(name, *(REFS[n] for n, _ in SOURCE)) + '][k jlstart[]]].' for name in ('hzda', 'hzdb', 'hzdc', 'hzdd'))
    return candidate(text, EXTRA + queries)


def source_model(doc, enabled=True, nonempty=True, gain=True, decrease=True, complete=True, variant='baseline'):
    model = revision.model_for(doc)
    supported = model['jksupported']
    old = {'p', 'notp', 'notq'}
    def corpus(holder, claim, stage):
        target = 'other' if variant == 'other_holder' and stage in ('gain', 'clean') else 'holder'
        items = old if stage == 'before' else old | {'q'} if stage == 'gain' else {'p'} | (set() if complete else {'notq'}) if stage == 'clean' else set()
        return holder == target and claim in items
    def outcomes(holder, plan, start, end):
        if holder != ('other' if variant == 'other_actor' else 'holder') or start != ('after' if variant == 'other_start' else 'before') or not nonempty: return False
        if plan == 'plan': return end == ('gain' if gain else 'before') or variant == 'risky' and end == 'before'
        if plan == 'backup': return end == ('clean' if decrease else 'before') or variant == 'risky' and end == 'before'
        return False
    model.update(jkcorpus=corpus,
        jksupported=lambda a, c, s: supported(a, c, 'after' if s in ('gain', 'clean') else s),
        jlstart=lambda: 'before',
        jlavailable=lambda a, p, s: enabled and (a, s) == ('holder', 'before') and p in ('plan', 'backup'),
        jloutcomes=outcomes)
    if variant == 'assessment_changed': model['jkassessment'] = lambda: 'w00'
    if variant == 'no_prior_errors':
        prior = model['jkcorpus']; model['jkcorpus'] = lambda a, c, s: prior(a, c, s) and (s != 'before' or c == 'p')
    return model


def source_checks(texts):
    docs = [source_setup(t) for t in texts]; cases = []
    for bits in product((False, True), repeat=5):
        enabled, nonempty, gain, decrease, complete = bits
        valid = not enabled or nonempty
        a, b, c = (valid and not (enabled and nonempty and success) for success in (gain, decrease, decrease and complete))
        want = [a, b, c, a and b]
        rows = [values(d, source_model(d, *bits), DOMAIN, SCENES) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Revision outcome was evaluated at the wrong stage: ' + repr((bits, rows, want)))
        cases.append(dict(bits=list(bits), results=want))
    contrasts = {}
    for variant, want in {
        'risky': [False] * 4, 'other_actor': [False] * 4, 'other_start': [False] * 4,
        'other_holder': [True] * 4, 'assessment_changed': [True] * 4,
        'no_prior_errors': [False, True, True, False],
    }.items():
        rows = [values(d, source_model(d, variant=variant), DOMAIN, SCENES) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Blocked revision contrast ' + variant + ': ' + repr(rows))
        contrasts[variant] = want
    for d in docs:
        for name in ('jlavailable', 'jloutcomes', 'jkcorpus', 'jksupported', 'jktruth', 'jkcomparisons'):
            model = source_model(d); model[name] = guarded(d)[name]
            try: values(d, model, DOMAIN, SCENES)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc): raise
            else: raise ValueError('Unknown opportunities or epistemic states filled in')
    return dict(cases=cases, contrasts=contrasts, standalone_agrees=True, unknown_relations_refused=True,
        separate_methods_can_satisfy_separate_goals=True, same_holder_baseline_and_assessment=True)


def causal_setup(text):
    doc = source_setup(text); doc['statements'] = []
    content = k('hzdd', *(REFS[n] for n, _ in SOURCE))
    trial = parse(format_graph(doc, 'compact') + 'q[e[r[' + content + ']][r[' + content + ']]].')
    result = trial['statements'][0]['body']['arguments'][0]
    specialized = specialize_definition(doc, 'hzcq', 'jlclosed', {1: result})
    doc = specialized.document
    closed = k('jlclosed', 'p jlagents', 'p jlcause')
    doc = parse(format_graph(doc, 'compact') + 'q[k jlaim[k jkholder[] r[' + closed + '] k jlstart[]]].' +
        'q[t[' + closed + '][k jlstart[]]].')
    direct = dict(kind='call', symbol='hzcq', arguments=[dict(kind='function_ref', symbol='jlagents'), result, dict(kind='function_ref', symbol='jlcause')])
    doc['statements'].append(dict(kind='ask', body=dict(kind='evaluate', content=direct, situation=dict(kind='call', symbol='jlstart', arguments=[]))))
    return parse(format_graph(doc, 'compact')), result, dict(bound_positions=specialized.bound_positions,
        disquotations_removed=specialized.disquotations_removed, expanded_definitions=specialized.expanded_definitions)


def causal_model(setup, caused=True, blocked=True, variant='baseline'):
    doc, result, _ = setup
    model = source_model(doc, gain=not blocked, decrease=not blocked)
    agents = () if variant == 'empty_agents' else ('alpha', 'act') if variant == 'nonhuman' else ('alpha', 'beta')
    expected = syntax(result)
    goal = syntax(doc['statements'][0]['body']['arguments'][1])
    model.update(aa=lambda a: a in ('alpha', 'beta'), jlagents=lambda a: a in agents,
        dg=lambda a, s: variant != 'no_occurrence' and (a, s) == ('act', 'before'),
        df=lambda a, act, s: a in agents and act == 'act' and s == 'before' and not (variant == 'missing_participant' and a == 'beta'),
        jlcause=lambda act, desc, s: caused and act == 'act' and s == ('after' if variant == 'other_time' else 'before') and desc.syntax == (('wrong',) if variant == 'other_content' else expected),
        jlaim=lambda a, desc, s: (a, desc.syntax, s) == ('holder', goal, 'before'))
    return model


def causal_checks(texts):
    setups = [causal_setup(t) for t in texts]; cases = []
    for caused, blocked in product((False, True), repeat=2):
        want = [True, caused and blocked, caused and blocked]
        rows = [values(s[0], causal_model(s, caused, blocked), DOMAIN, SCENES) for s in setups]
        if rows != [want] * len(setups): raise ValueError('Purpose or co-occurrence became achieved causal obstruction')
        cases.append(dict(caused=caused, blocked=blocked, results=want))
    contrasts = {}
    for variant in ('empty_agents', 'nonhuman', 'no_occurrence', 'missing_participant', 'other_time', 'other_content'):
        rows = [values(s[0], causal_model(s, variant=variant), DOMAIN, SCENES) for s in setups]
        if rows != [[True, False, False]] * len(setups): raise ValueError('Causal linkage contrast ' + variant)
        contrasts[variant] = rows[0]
    for s in setups:
        doc, _, _ = s
        model = guarded(doc); actual = causal_model(s)
        model.update({n: actual[n] for n in ('jkholder', 'jlstart', 'jlaim')})
        only_goal = deepcopy(doc); only_goal['statements'] = only_goal['statements'][:1]
        if values(only_goal, model, DOMAIN, SCENES) != [True]: raise ValueError('Unrealized obstruction could not be a goal')
        try: values(doc, model, DOMAIN, SCENES)
        except ValueError as exc:
            if 'Unrelated primitive' not in str(exc): raise
        else: raise ValueError('Unknown causal achievement inferred')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Closed causal obstruction changed')
    return dict(cases=cases, contrasts=contrasts, specialization=[s[2] for s in setups],
        dynamic_and_specialized_agree=True, closed_goal_roundtrips=True, unknown_goal_not_evaluated=True,
        generation_identity_not_supplied=True, causation_is_explicit_input=True)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Stored blocked revision differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Blocked revision roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = dict(characters=len(text), statements=len(doc['statements']))
    doc, parent = parse(texts[1]), parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']: raise ValueError('Parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0013')
    segments = []
    for phrase, symbols in (('in einen Zustand zu setzen', ['hzcq', 'hzdd']), ('darin es ihm unmöglich werden muß', ['rja', 'rjb', 'hzda', 'hzdb', 'hzdd'])):
        if unit['text'].count(phrase) != 1: raise ValueError('Ambiguous source phrase')
        start = unit['text'].index(phrase)
        segments.append(dict(unit=unit['id'], unit_sha256=unit['text_sha256'], status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase, definitions=symbols))
    paths = [*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_blocked_revision.py', 'scripts/check_blocked_revision.py', 'scripts/check_epistemic_revision.py',
        'scripts/check_conditional_release.py', 'scripts/check_described_appraisals.py', 'scripts/check_public_assessment.py',
        'scripts/check_rod_setup.py', 'noema/finite_semantics.py', 'noema/extraction.py', 'noema/specialization.py',
        'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_blocked_revision_and_causal_result', documents=documents, sizes=sizes,
        generic=generic_checks([texts[0], texts[2]]), source=source_checks(texts[1:]), causation=causal_checks(texts[1:]),
        alignment=dict(segments=segments, semantic_completion=False), new_definitions=6, new_primitives=0, new_author_statements=0,
        parent_preserved=True, roundtrips=True, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in paths})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); options = parser.parse_args()
    report = build_report()
    if options.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Blocked revision report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream: json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Possible revision outcomes, separate goals, caused results and unknown inputs checked')


if __name__ == '__main__': main()
