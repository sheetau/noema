"""Check ordered binding and the complete modal-result/goal/policy connection."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.extraction import extract_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from noema.specialization import specialize_definition
from scripts.check_assessed_payments import description
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_policy_norms import seq
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts import check_necessary_futures as modal
from scripts import check_parameterized_goals as bound
from scripts.compose_limits import call as k, app, op
from scripts.compose_origin_clock import v
from scripts.compose_situated_criticism import params, args
from scripts.compose_parameterized_goals import CASE, case_bindings, case_shape, PRODUCES, UNIVERSAL_SOURCE
from scripts.compose_bound_revision import ROOT, PARENT, BUILDERS, MODAL, CONFIG, FIVE

REPORT = ROOT / 'reports/bound-revision-v1.json'
EXTRA = '''r jbcase[] j[a].r jbholder[] a.r jblater[] a.
r jbpremise[a a a a a d] c.
d jbconditions[firstgroup a nextgroup a earlier a later a agreement a] e[b scene[
k jbpremise[v firstgroup v nextgroup v earlier v later v agreement v scene]]].'''
REFS = modal.REFS | dict(conditions='p jbconditions')
MODAL_CASE = ('other', 'holder', 'other', 'later', 'plan')


def roundtrips(doc):
    for notation in ('full', 'compact'):
        text = format_graph(doc, notation)
        if parse(text) != doc or parse(decode(encode(text, 'v2'))) != doc:
            raise ValueError('Bound revision roundtrip differs')


def adapter_checks(text):
    base = extract_document(parse(text), roots=['rj3'], statement_indices=[]).document
    extra = 'r jbtest[a a a a a d] c.d jbtarget[firstgroup a nextgroup a earlier a later a agreement a] e[b scene[k jbtest[v firstgroup v nextgroup v earlier v later v agreement v scene]]].'
    tuples = list(product(('left', 'right'), repeat=5))
    literals = ['l[a][' + ' '.join('k jb' + x + '[]' for x in row) + ']' for row in tuples]
    invalid = ['l[a][]', 'l[a][k jbleft[]]'] + ['l[a][' + ' '.join(['k jbleft[]'] * n) + ']' for n in (4, 6)]
    queries = ''.join('q[t[' + app(k('rj3', 'p jbtarget'), row) + '][k jbscene[]]].' for row in literals + invalid)
    doc = candidate(format_graph(base, 'compact'), extra + 'r jbleft[] a.r jbright[] a.r jbscene[] d.' + queries)
    count = 0
    for target, scene in product(tuples, ('now', 'later')):
        model = guarded(doc); model.update(jbleft=lambda: 'left', jbright=lambda: 'right', jbscene=lambda: scene,
            jbtest=lambda *a: a[:-1] == target and a[-1] == 'now')
        want = [row == target and scene == 'now' for row in tuples] + [False] * len(invalid)
        if values(doc, model, ('left', 'right'), ('now', 'later')) != want:
            raise ValueError('Five-slot fold changed order, multiplicity, shape or context')
        count += 1
    roundtrips(doc)
    return dict(models=count, valid_sequences_per_model=32, invalid_lengths=[0, 1, 4, 6],
        independent_positional_oracle=True, repeated_elements_preserved=True, general_higher_order_proof=False)


def modal_setup(text):
    queries = ''
    for name, old in (('hzdu', 'hzdh'), ('hzdv', 'hzdi'), ('hzdw', 'hzdj')):
        expression = app(k(name, *(REFS[n] for n, _ in MODAL)), 'k jbcase[]')
        direct = modal.REFS | dict(holder='k jbholder[]', later='k jblater[]', condition=app('p jbconditions', *['k jb' + n + '[]' for n, _ in CASE]))
        queries += 'q[t[' + expression + '][k jmodalcontext[]]].q[t[' + k(old, *(direct[n] for n, _ in modal.SOURCE)) + '][k jmodalcontext[]]].'
    constants = ''.join('r jb' + n + '[] a.' for n, _ in CASE if n != 'later')
    return candidate(text, modal.blocked.EXTRA + modal.EXTRA + EXTRA + constants + queries)


def modal_model(doc, bits=(True, True, True), variant='baseline'):
    applicable, left, right = bits
    closed = modal.source_model(doc, (True, True, applicable, applicable, left, right))
    opened = modal.source_model(doc, (True, True, applicable, applicable, False, False))
    model = closed.copy()
    # Both holders are interpreted. The second holder has actual improvement options.
    for name in ('jkcorpus', 'jksupported', 'jlavailable', 'jloutcomes'):
        model[name] = lambda owner, *a, name=name: (opened if owner == 'other' else closed)[name]('holder', *a)
    chosen = list(MODAL_CASE)
    if variant == 'other_holder': chosen[1] = 'other'
    if variant == 'other_epoch': chosen[3] = 'other'
    if variant == 'other_contract': chosen[4] = 'backup'
    for (name, _), value in zip(CASE, chosen): model['jb' + name] = lambda value=value: value
    model.update(jbcase=lambda: seq(chosen), jbholder=lambda: chosen[1], jblater=lambda: chosen[3],
        jbpremise=lambda *a: a[4] == 'plan' and closed['jmodalpremise'](a[-1]))
    return model


def modal_checks(texts):
    docs = [modal_setup(t) for t in texts]; cases = []
    for bits in product((False, True), repeat=3):
        applicable, left, right = bits
        nonvacuous = applicable and left and right
        want = [nonvacuous] * 4 + [not applicable or left and right] * 2
        rows = [values(d, modal_model(d, bits), modal.DOMAIN, modal.SCENES) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Bound modal content differs from its direct application')
        cases.append(dict(bits=list(bits), results=want))
    contrasts = {}
    for variant in ('other_holder', 'other_epoch', 'other_contract'):
        want = [False] * 4 + ([True] * 2 if variant == 'other_contract' else [False] * 2)
        rows = [values(d, modal_model(d, variant=variant), modal.DOMAIN, modal.SCENES) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Bound modal contrast ' + variant + ': ' + repr(rows))
        contrasts[variant] = want
    return dict(cases=cases, contrasts=contrasts, direct_application_agrees=True, standalone_agrees=True)


CHAIN_EXTRA = '''r jbproduces[''' + PRODUCES[2:-3] + '''] c.
r jbpact[a] c.r jballocation[a a] j[a].
r jbselect[a i[h[j[a]] e] i[h[j[a]] e]] i[h[j[a]] e].
r jbsource[] a.r jbrole[] a.r jbcontext[] d.r jbeligible[a a a a a d] c.'''
CHAIN_CASE = ('oldgroup', 'newgroup', 'early', 'late', 'pact')


def assemble(text, constructor='hzdu'):
    extra = bound.solemn.EXTRA + bound.cohorts.EXTRA + modal.blocked.EXTRA + modal.EXTRA + EXTRA + bound.GOAL_EXTRA + CHAIN_EXTRA
    doc = candidate(text, extra)
    refs = REFS | dict(periods='p jperiods')
    result_text = k(constructor, *(refs[n] for n, _ in MODAL))
    result = description(doc, result_text)
    specialized = specialize_definition(doc, 'hzdr', 'jbcausal', {1: result}); doc = specialized.document
    parties = 'i[person a][' + op('w', k('jbpact', v('agreement')), k('jg', v('person'), v('context'))) + ']'
    cause = k('jbcausal', parties, case_bindings(), case_shape(), 'p jbproduces')
    goal_text = k('rj3', 'i[' + params(CASE) + '][b context[' + op('t', cause, v('context')) + ']]')
    goal = description(doc, goal_text)
    refs = bound.REFS | bound.cohorts.REFS | dict(history='p jj', goal='r[' + goal_text + ']')
    refs['terms'] = 'i[agreement a][k jbselect[v agreement r[p jq] r[p jr]]]'
    refs['parties'] = 'i[agreement a][i[person a context d][' + op('w', k('jbpact', v('agreement')), k('jg', v('person'), v('context'))) + ']]'
    refs['proponents'] = 'i[agreement a][i[person a context d][' + op('w', k('jbpact', v('agreement')), k('jwproponents', v('person'), v('context'))) + ']]'
    refs['arguments'] = 'i[agreement a][i[person a][k jballocation[v agreement v person]]]'
    for name in ('authority', 'formula'): refs[name] = 'i[agreement a][' + refs[name] + ']'
    policy_text = k('hzdx', *(refs[n] for n, _ in CONFIG))
    policy = description(doc, policy_text)
    return dict(document=doc, result=result, goal=goal, policy=policy, result_text=result_text, goal_text=goal_text, policy_text=policy_text,
        disquotations_removed=specialized.disquotations_removed, bound_positions=specialized.bound_positions)


def query_policy(setup):
    return parse(format_graph(setup['document'], 'compact') + 'q[t[' + app(setup['policy_text'], 'k jbcase[]') + '][k je[]]].')


def policy_model(doc, setup, aimed=True, solemnity=True, variant='baseline'):
    model = bound.purpose_model(doc, aimed, solemnity, source=True)
    selected = list(CHAIN_CASE)
    if variant == 'other_group': selected[1] = 'oldgroup'
    if variant == 'other_epoch': selected[3] = 'early'
    if variant == 'other_contract': selected[4] = 'other'
    if variant == 'empty': selected = []
    if variant == 'extra': selected.append('other')
    expected = tuple(reversed(CHAIN_CASE)) if variant == 'reversed_aim' else CHAIN_CASE
    model.update(jbcase=lambda: seq(selected), jbpact=lambda pact: pact == 'pact',
        jballocation=lambda pact, person: model['jh'](person) if pact == 'pact' else seq(()),
        jbselect=lambda pact, first, second: first if pact == 'pact' else second,
        jbaims=lambda p, a, g, b, s: aimed and (p, a, s) == ('alpha', 'acta', 'first') and g.syntax == syntax(setup['goal']) and b.items == expected)
    return model


def chain_checks(texts):
    setups = [assemble(t) for t in texts]; docs = [query_policy(s) for s in setups]; cases = []
    for aimed, solemnity in product((False, True), repeat=2):
        rows = [values(d, policy_model(d, s, aimed, solemnity), bound.cohorts.DOMAIN, bound.cohorts.SCENES) for d, s in zip(docs, setups)]
        if rows != [[aimed and solemnity]] * len(docs): raise ValueError('Composed policy executed its unknown modal/causal goal')
        cases.append(dict(aimed=aimed, solemnity=solemnity, result=aimed and solemnity))
    contrasts = {}
    for variant in ('other_group', 'other_epoch', 'other_contract', 'reversed_aim', 'empty', 'extra'):
        rows = [values(d, policy_model(d, s, variant=variant), bound.cohorts.DOMAIN, bound.cohorts.SCENES) for d, s in zip(docs, setups)]
        if rows != [[False]] * len(docs): raise ValueError('Complete bound policy contrast ' + variant)
        contrasts[variant] = False
    for doc in docs: roundtrips(doc)
    # The two alternative modal readings also form fully closed policies.
    alternatives = {}
    for constructor in ('hzdv', 'hzdw'):
        built = assemble(texts[-1], constructor); doc = query_policy(built)
        if values(doc, policy_model(doc, built), bound.cohorts.DOMAIN, bound.cohorts.SCENES) != [True]:
            raise ValueError('Alternative modal policy could not be represented')
        roundtrips(doc); alternatives[constructor] = True
    return dict(cases=cases, contrasts=contrasts, alternative_readings=alternatives,
        unknown_goal_contents_not_executed=True, same_case_for_goal_and_policy=True, closed_roundtrips=True,
        disquotations_removed=[s['disquotations_removed'] for s in setups], bound_positions=[s['bound_positions'] for s in setups]), setups


def normative_checks(setups):
    targets = (('left', 'right', 'left', 'right', 'left'), ('left', 'right', 'left', 'right', 'right'))
    docs = []
    for s in setups:
        refs = dict(source='k jbsource[]', role='k jbrole[]', description='r[' + s['policy_text'] + ']', eligible='p jbeligible')
        queries = ''.join('q[t[' + k(n, *(refs[x] for x, _ in UNIVERSAL_SOURCE)) + '][k jbcontext[]]].' for n in ('hzds', 'hzdt'))
        docs.append(parse(format_graph(s['document'], 'compact') + queries))
    cases = []
    for bits in product((False, True), repeat=4):
        f1, f2, p1, p2 = bits; want = [f1 and f2, not p1 and not p2]
        for doc, setup in zip(docs, setups):
            model = guarded(doc); expected = syntax(setup['policy'])
            def norm(kind, source, person, role, desc, bindings, sign, context):
                if (source, person, role, desc.syntax, context) != ('left', 'left', 'right', expected, 'now') or bindings.items not in targets: return False
                index = targets.index(bindings.items)
                return (f1, f2)[index] and not sign if kind == 'required' else (p1, p2)[index] and sign
            model.update(jbsource=lambda: 'left', jbrole=lambda: 'right', jbcontext=lambda: 'now',
                jbeligible=lambda *a: a[:-1] in targets and a[-1] == 'now',
                h7k=lambda *a: norm('required', *a), h7l=lambda *a: norm('allowed', *a))
            if values(doc, model, ('left', 'right'), ('now',)) != want: raise ValueError('Universal norm lost the complete policy target')
        cases.append(dict(bits=list(bits), results=want))
    return dict(cases=cases, same_full_policy_for_all_contracts=True,
        unknown_contract_formation_and_goal_not_executed=True, quoted_policy_not_a_primitive_placeholder=True)


def achieved_checks(setups):
    docs = [parse(format_graph(s['document'], 'compact') + 'q[t[' + app(s['goal_text'], 'k jbcase[]') + '][k jmodalcontext[]]].') for s in setups]
    def model_for(doc, setup, bits=(True,) * 4, variant='baseline'):
        actual, occurs, participates, causes = bits
        model = modal_model(doc, (True, actual, actual))
        expected = syntax(setup['result'])
        model.update(jperiods=model['jmodalperiods'], jbpact=lambda pact: pact == 'plan',
            jg=lambda person, context: variant != 'empty_agents' and (person, context) == ('other', 'now'),
            aa=lambda person: variant != 'nonhuman' and person == 'other',
            dg=lambda act, context: occurs and (act, context) == ('plan', 'now'),
            df=lambda person, act, context: participates and (person, act, context) == ('other', 'backup' if variant == 'other_act' else 'plan', 'now'),
            jbproduces=lambda act, target, bindings, context: causes and variant != 'other_result'
                and target.syntax == expected and bindings.items == (tuple(reversed(MODAL_CASE)) if variant == 'other_bindings' else MODAL_CASE)
                and (act, context) == ('plan', 'endleft' if variant == 'other_time' else 'now'))
        # The direct-reference constants belong only to modal_setup, not this document.
        names = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
        return {n: x for n, x in model.items() if n in names}
    cases = []
    for bits in product((False, True), repeat=4):
        rows = [values(d, model_for(d, s, bits), modal.DOMAIN, modal.SCENES) for d, s in zip(docs, setups)]
        if rows != [[all(bits)]] * len(docs): raise ValueError('Complete causal goal omitted its modal result or shared act')
        cases.append(dict(bits=list(bits), result=all(bits)))
    contrasts = {}
    for variant in ('empty_agents', 'nonhuman', 'other_act', 'other_result', 'other_bindings', 'other_time'):
        rows = [values(d, model_for(d, s, variant=variant), modal.DOMAIN, modal.SCENES) for d, s in zip(docs, setups)]
        if rows != [[False]] * len(docs): raise ValueError('Complete causal goal contrast ' + variant)
        contrasts[variant] = False
    for doc, setup in zip(docs, setups):
        for name in ('jbproduces', 'jbpremise', 'jloutcomes'):
            model = model_for(doc, setup); model[name] = guarded(doc)[name]
            try: values(doc, model, modal.DOMAIN, modal.SCENES)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc): raise
            else: raise ValueError('Unknown cause or modal result supplied by default')
    return dict(cases=cases, contrasts=contrasts, same_modal_result_executed=True, unknown_relations_refused=True,
        joint_agents_required=True, standalone_agrees=True)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Stored bound revision differs')
        roundtrips(doc); documents[basis['document']] = audit_basis(doc, basis)
        sizes[stem] = dict(characters=len(text), statements=len(doc['statements']))
    doc, parent = parse(texts[0]), parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']: raise ValueError('Parent changed')
    chain, setups = chain_checks(texts)
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0013')
    phrase = 'Ein Zeitalter kann sich nicht verbünden und darauf verschwören, das folgende in einen Zustand zu setzen, darin es ihm unmöglich werden muß, seine (vornehmlich so sehr angelegentliche) Erkenntnisse zu erweitern, von Irrthümern zu reinigen'
    if unit['text'].count(phrase) != 1: raise ValueError('Ambiguous source phrase')
    # Keep only the individually supported spans; the parenthetical emphasis remains open.
    phrases = ['Ein Zeitalter kann sich nicht verbünden und darauf verschwören', 'das folgende', 'in einen Zustand zu setzen', 'darin es ihm unmöglich werden muß', 'Erkenntnisse zu erweitern', 'von Irrthümern zu reinigen']
    segments = []
    for part in phrases:
        start = unit['text'].index(part, unit['text'].index(phrase))
        segments.append(dict(unit=unit['id'], unit_sha256=unit['text_sha256'], status='explicit_interpretive_annotation',
            range=[start, start + len(part)], text=part, definitions=['rj3', 'hzdu', 'hzdv', 'hzdw', 'hzdx']))
    paths = [*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_bound_revision.py', 'scripts/check_bound_revision.py', 'scripts/compose_parameterized_goals.py',
        'scripts/check_parameterized_goals.py', 'scripts/check_necessary_futures.py', 'scripts/check_assessed_payments.py',
        'scripts/check_conditional_release.py', 'scripts/check_described_appraisals.py', 'scripts/check_policy_norms.py',
        'scripts/check_public_assessment.py', 'scripts/check_rod_setup.py', 'noema/finite_semantics.py',
        'noema/extraction.py', 'noema/specialization.py', 'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_complete_bound_revision_policy_connection', documents=documents, sizes=sizes,
        adapter=adapter_checks(texts[1]), modal=modal_checks(texts), chain=chain, norms=normative_checks(setups), achieved=achieved_checks(setups),
        alignment=dict(segments=segments, semantic_completion=False), new_definitions=5, new_primitives=0,
        new_author_statements=0, parent_preserved=True, roundtrips=True,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in paths})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); options = parser.parse_args()
    report = build_report()
    if options.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Bound revision report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream: json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Ordered bindings, modal improvement results and complete quoted policy norms checked')


if __name__ == '__main__': main()
