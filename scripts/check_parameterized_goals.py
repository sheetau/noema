"""Check template/binding identity, unachieved goals and quantified norm cases."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from noema.specialization import specialize_definition
from scripts.check_closed_policies import quoted
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_policy_norms import seq
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts import check_solemn_undertakings as solemn
from scripts import check_successive_cohorts as cohorts
from scripts.compose_limits import call as k
from scripts.compose_parameterized_goals import ROOT, PARENT, BUILDERS, GOAL, ACT, PURPOSE, SOLEMN, CAUSE, CAUSAL_CONTENT, SOURCE, UNIVERSAL, UNIVERSAL_SOURCE, AIMS, PRODUCES, RULE

REPORT = ROOT / 'reports/parameterized-goals-v1.json'
GOAL_EXTRA = '''r jbgoalbindings[] j[a].r jbgoalvalid[j[a]] c.r jbgoaltruth[j[a] d] c.
d jbgoal[bindings j[a]] e[b scene[k jbgoaltruth[v bindings v scene]]].
d jbalias[bindings j[a]] e[b scene[k jbgoaltruth[v bindings v scene]]].
r jbaims[''' + AIMS[2:-3] + '''] c.'''
REFS = solemn.REFS | dict(goal='r[p jbgoal]', goalbindings='k jbgoalbindings[]', goalvalid='p jbgoalvalid', aims='p jbaims')


def purpose_setup(text, source=False):
    if source:
        refs = REFS | cohorts.REFS | dict(context='k je[]', history='p jj')
        return candidate(text, solemn.EXTRA + cohorts.EXTRA + GOAL_EXTRA + 'q[' + k('hzdq', *(refs[n] for n, _ in SOURCE)) + '].')
    return candidate(text, solemn.EXTRA + GOAL_EXTRA + ''.join('q[' + k(name, *(REFS[n] for n, _ in fields)) + '].' for name, fields in
        (('rjt', ACT + GOAL), ('rju', PURPOSE), ('rjv', SOLEMN))))


def purpose_model(doc, aimed=True, solemnity=True, variant='baseline', source=False):
    model = solemn.model_for(doc, bits=(solemnity,) * 4)
    if source:
        c = cohorts.cohort_model(doc, variant if variant in ('act_outside', 'party_outside') else 'baseline')
        names = ('jearly', 'jlate', 'jfirstgroup', 'jnextgroup', 'jcontext', 'jepochs', 'jhistory', 'jorder', 'jperiods', 'jpopulation', 'jhuman', 'jpresent', 'jbelongs')
        model.update({n: c[n] for n in names}); model['jj'] = c['jhistory']; model['aa'] = c['jhuman']
        model['ic'] = lambda a, b, s: s == 'now' and c['jorder'](a, b)
    bindings = ('oldgroup', 'newgroup', 'early', 'late', 'pact') if source else ('alpha', 'beta')
    expected = tuple(reversed(bindings)) if variant == 'reversed_goal_bindings' else bindings
    if variant == 'different_contract' and source: expected = (*bindings[:-1], 'other')
    target = syntax(quoted('function_ref', 'jbalias' if variant == 'alias' else 'jbgoal'))
    record = ('beta', 'acta', 'first') if variant == 'wrong_person' else ('alpha', 'actb', 'first') if variant == 'wrong_act' else ('alpha', 'acta', 'second') if variant == 'wrong_time' else ('alpha', 'acta', 'first')
    model.update(jbgoalbindings=lambda: seq((*bindings, 'other') if variant == 'invalid_shape' else bindings),
        jbgoalvalid=lambda b: len(b.items) == len(bindings),
        jbaims=lambda p, a, g, b, s: aimed and (p, a, s) == record and g.syntax == target and b.items == expected)
    return model


def purpose_checks(texts, source=False):
    docs = [purpose_setup(t, source) for t in texts]; cases = []
    domain = cohorts.DOMAIN if source else solemn.mutual.PEOPLE
    for aimed, solemnity in product((False, True), repeat=2):
        want = [aimed and solemnity] if source else [aimed, aimed, aimed and solemnity]
        rows = [values(d, purpose_model(d, aimed, solemnity, source=source), domain, solemn.mutual.SCENES) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Bound purpose confused with solemnity or achievement')
        cases.append(dict(aimed=aimed, solemnity=solemnity, results=want))
    contrasts = {}
    variants = ('alias', 'reversed_goal_bindings', 'wrong_person', 'wrong_act', 'wrong_time') + (('different_contract', 'act_outside', 'party_outside') if source else ('invalid_shape',))
    for variant in variants:
        want = [False] if source else [False] * 3
        rows = [values(d, purpose_model(d, variant=variant, source=source), domain, solemn.mutual.SCENES) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Bound purpose contrast ' + variant + ': ' + repr(rows))
        contrasts[variant] = want
    for d in docs:
        model = purpose_model(d, source=source); model['jbaims'] = guarded(d)['jbaims']
        try: values(d, model, domain, solemn.mutual.SCENES)
        except ValueError as exc:
            if 'Unrelated primitive' not in str(exc): raise
        else: raise ValueError('Unknown bound goal relation invented')
    return dict(cases=cases, contrasts=contrasts, standalone_agrees=True, goal_truth_not_executed=True,
        same_template_and_bindings_required=True, unknown_aims_refused=True)


CAUSE_EXTRA = GOAL_EXTRA + '''r jbagents[a] c.r jbact[] a.r jbcontext[] d.
r jboccurs[a d] c.r jbpart[a a d] c.r jbproduces[''' + PRODUCES[2:-3] + '''] c.'''
CAUSE_REFS = dict(agents='p jbagents', act='k jbact[]', result='r[p jbgoal]', bindings='k jbgoalbindings[]',
    valid='p jbgoalvalid', context='k jbcontext[]', occurs='p jboccurs', participates='p jbpart', produces='p jbproduces')


def causal_setup(text):
    queries = 'q[' + k('rjw', *(CAUSE_REFS[n] for n, _ in CAUSE)) + '].q[t[' + k('rjx', *(CAUSE_REFS[n] for n, _ in CAUSAL_CONTENT)) + '][k jbcontext[]]].'
    return candidate(text, CAUSE_EXTRA + queries)


def causal_model(doc, bits=(True,) * 5, variant='baseline'):
    occurs, first, second, causes, actual = bits; model = guarded(doc)
    target = syntax(quoted('function_ref', 'jbalias' if variant == 'alias' else 'jbgoal'))
    members = () if variant == 'empty_agents' else ('alpha', 'beta')
    expected = ('beta', 'alpha') if variant == 'other_bindings' else ('alpha', 'beta')
    model.update(jbagents=lambda p: p in members, jbact=lambda: 'acta', jbcontext=lambda: 'now',
        jbgoalbindings=lambda: seq(('alpha',) if variant == 'invalid_shape' else ('alpha', 'beta')),
        jbgoalvalid=lambda b: len(b.items) == 2,
        jboccurs=lambda a, s: occurs and (a, s) == ('acta', 'now'),
        jbpart=lambda p, a, s: (a, s) == ('actb' if variant == 'other_act' else 'acta', 'now') and (p == 'alpha' and first or p == 'beta' and second),
        jbproduces=lambda a, d, b, s: causes and (a, s) == ('acta', 'future' if variant == 'other_time' else 'now') and d.syntax == target and b.items == expected,
        jbgoaltruth=lambda b, s: actual)
    return model


def causal_checks(texts):
    docs = [causal_setup(t) for t in texts]; cases = []
    for bits in product((False, True), repeat=5):
        rows = [values(d, causal_model(d, bits), solemn.mutual.PEOPLE, solemn.mutual.SCENES) for d in docs]
        if rows != [[all(bits)] * 2] * len(docs): raise ValueError('Bound causal result separated from its actual arguments')
        cases.append(dict(bits=list(bits), results=rows[0]))
    contrasts = {}
    for variant in ('alias', 'other_bindings', 'empty_agents', 'invalid_shape', 'other_act', 'other_time'):
        rows = [values(d, causal_model(d, variant=variant), solemn.mutual.PEOPLE, solemn.mutual.SCENES) for d in docs]
        if rows != [[False, False]] * len(docs): raise ValueError('Bound causal contrast ' + variant)
        contrasts[variant] = rows[0]
    for d in docs:
        for name in ('jbproduces', 'jbgoaltruth', 'jbgoalvalid'):
            model = causal_model(d); model[name] = guarded(d)[name]
            try: values(d, model, solemn.mutual.PEOPLE, solemn.mutual.SCENES)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc): raise
            else: raise ValueError('Unknown bound causal result inferred')
        bare = deepcopy(d); bare['statements'] = []
        specialized = specialize_definition(bare, 'rjx', 'jbclosed', {1: quoted('function_ref', 'jbgoal')})
        doc = specialized.document
        template = 'i[targets j[a]][' + k('jbclosed', 'p jbagents', 'v targets', 'p jbgoalvalid', 'p jboccurs', 'p jbpart', 'p jbproduces') + ']'
        doc = parse(format_graph(doc, 'compact') + 'q[k jbaims[k jbact[] k jbact[] r[' + template + '] k jbgoalbindings[] k jbcontext[]]].')
        goal = doc['statements'][0]['body']['arguments'][2]
        model = guarded(doc); expected = syntax(goal)
        model.update(jbact=lambda: 'acta', jbgoalbindings=lambda: seq(('alpha', 'beta')), jbcontext=lambda: 'now',
            jbaims=lambda p, a, g, b, s: (p, a, g.syntax, b.items, s) == ('acta', 'acta', expected, ('alpha', 'beta'), 'now'))
        if values(doc, model, solemn.mutual.PEOPLE, solemn.mutual.SCENES) != [True]: raise ValueError('Variable-bound causal purpose executed unknown contents')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Bound causal template roundtrip changed')
    return dict(cases=cases, contrasts=contrasts, standalone_agrees=True, unknown_cause_and_truth_refused=True,
        specialization_retains_variable_bindings=True, closed_template_roundtrips=True)


UNIV_EXTRA = GOAL_EXTRA + '''r jusource[] a.r jurole[] a.r juctx[] d.
r jueligible[a a a a a d] c.r jurequired[''' + RULE[2:-3] + '] c.r juallowed[' + RULE[2:-3] + '] c.'
UNIV_REFS = dict(source='k jusource[]', role='k jurole[]', description='r[p jbgoal]', context='k juctx[]',
    eligible='p jueligible', required='p jurequired', allowed='p juallowed')


def universal_checks(texts, source=False):
    queries = ''.join('q[t[' + k(n, *(UNIV_REFS[x] for x, _ in UNIVERSAL_SOURCE)) + '][k juctx[]]].' for n in ('hzds', 'hzdt')) if source else ''.join('q[' + k(n, *(UNIV_REFS[x] for x, _ in UNIVERSAL)) + '].' for n in ('rjy', 'rjz'))
    queries += 'q[k rj2[k juctx[] p jueligible]].'
    docs = [candidate(t, UNIV_EXTRA + queries) for t in texts]
    targets = (('left', 'right', 'left', 'right', 'left'), ('left', 'right', 'left', 'right', 'right'))
    expected = syntax(quoted('function_ref', 'jbgoal')); cases = []
    for bits in product((False, True), repeat=6):
        selected = bits[:2]; forbidden = bits[2:4]; permitted = bits[4:]
        want = [all(not s or b for s, b in zip(selected, forbidden)), all(not s or not p for s, p in zip(selected, permitted)), any(selected)]
        for doc in docs:
            model = guarded(doc)
            def eligible(*a): return a[-1] == 'now' and a[:-1] in targets and selected[targets.index(a[:-1])]
            def norm(kind, source_, person, role, desc, bindings, sign, context):
                if (source_, person, role, desc.syntax, context) != ('left', 'left', 'right', expected, 'now') or bindings.items not in targets: return False
                return forbidden[targets.index(bindings.items)] and not sign if kind == 'required' else permitted[targets.index(bindings.items)] and sign
            model.update(jusource=lambda: 'left', jurole=lambda: 'right', juctx=lambda: 'now', jueligible=eligible,
                jurequired=lambda *a: norm('required', *a), juallowed=lambda *a: norm('allowed', *a))
            if source: model.update(h7k=model['jurequired'], h7l=model['juallowed'])
            if values(doc, model, ('left', 'right'), ('now',)) != want: raise ValueError('Universal denial checked only one contract or inferred existence')
        cases.append(dict(bits=list(bits), results=want))
    for doc in docs:
        for name in ('jueligible', 'h7k' if source else 'jurequired', 'h7l' if source else 'juallowed'):
            model = guarded(doc); model.update(jusource=lambda: 'left', jurole=lambda: 'right', juctx=lambda: 'now',
                jueligible=lambda *a: True, jurequired=lambda *a: False, juallowed=lambda *a: False)
            if source: model.update(h7k=lambda *a: False, h7l=lambda *a: False)
            model[name] = guarded(doc)[name]
            try: values(doc, model, ('left', 'right'), ('now',))
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc): raise
            else: raise ValueError('Unknown universal scope or norm guessed')
    return dict(cases=cases, quantified_individual_positions=5, combinations_per_model=32, standalone_agrees=True,
        all_declared_domain_combinations_checked=True, real_world_scope_completeness_not_proven=True,
        actual_contract_formation_not_required=True, unknown_scope_and_norms_refused=True)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Stored parameterized goal differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Parameterized goal roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = dict(characters=len(text), statements=len(doc['statements']))
    doc, parent = parse(texts[1]), parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']: raise ValueError('Parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0013')
    phrase = 'Ein Zeitalter kann sich nicht verbünden und darauf verschwören'
    if unit['text'].count(phrase) != 1: raise ValueError('Ambiguous source phrase')
    start = unit['text'].index(phrase)
    segment = dict(unit=unit['id'], unit_sha256=unit['text_sha256'], status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase, definitions=['rju', 'rjv', 'rjy', 'rjz', 'rj2', 'hzdq', 'hzds', 'hzdt'])
    paths = [*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_parameterized_goals.py', 'scripts/check_parameterized_goals.py', 'scripts/check_solemn_undertakings.py',
        'scripts/check_successive_cohorts.py', 'scripts/check_closed_policies.py', 'scripts/check_conditional_release.py',
        'scripts/check_described_appraisals.py', 'scripts/check_policy_norms.py', 'scripts/check_public_assessment.py',
        'scripts/check_rod_setup.py', 'noema/finite_semantics.py', 'noema/extraction.py', 'noema/specialization.py',
        'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_parameterized_goals_and_universal_denial', documents=documents, sizes=sizes,
        generic=purpose_checks([texts[0], texts[2]]), source=purpose_checks(texts[1:], True),
        causation=causal_checks([texts[0], texts[2]]), universal=universal_checks([texts[0], texts[2]]),
        source_universal=universal_checks(texts[1:], True), alignment=dict(segments=[segment], semantic_completion=False),
        new_definitions=12, new_primitives=0, new_author_statements=0, parent_preserved=True, roundtrips=True,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in paths})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); options = parser.parse_args()
    report = build_report()
    if options.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Parameterized goal report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream: json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Bound goal/cause templates, five-position source cases and universal normative conditions checked')


if __name__ == '__main__': main()
