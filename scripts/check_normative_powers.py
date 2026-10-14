"""Check norm creation/repeal, constitutive control, permission and exercise."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.description_templates import apply_description
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_closed_policies import quoted
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_policy_norms import seq
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts.compose_limits import call as k
from scripts.compose_normative_powers import ROOT, PARENT, BUILDERS, EFFECT, TRANSITION, POWER, ACTUAL, SOURCE, PERMITTED, CONTROL, EDGE, RULE, TRUE

REPORT = ROOT / 'reports/normative-powers-v1.json'
CONSTANTS = {'framework': 'framework', 'actor': 'holder', 'capacity': 'capacity', 'source': 'contract',
    'person': 'beneficiary', 'role': 'role', 'assessor': 'assessor', 'first': 'first', 'second': 'second', 'author': 'author'}
DOMAIN = tuple(CONSTANTS.values()) + ('other',)
SCENES = ('before', 'after', 'alternative')
EXTRA = ''.join('r jg' + n + '[] a.' for n in CONSTANTS) + '''
r jgstart[] d.r jgend[] d.r jgstatus[] c.r jgpolarity[] c.
r jgbindings[] j[a].r jgexercisebindings[] j[a].r jgvalid[j[a]] c.r jgexercisevalid[j[a]] c.
r jgcontrolled[''' + CONTROL[2:-3] + '''] c.r jgperformed[''' + CONTROL[2:-3] + '''] c.
r jgrecognizes[''' + EDGE[2:-3] + '''] c.r jgrealized[d d] c.r jgrelation[''' + RULE[2:-3] + '''] c.
r jgpolicytruth[j[a] d] c.r jgexercisetruth[j[a] d] c.
d jgpolicy[bindings j[a]] e[b scene[k jgpolicytruth[v bindings v scene]]].
d jgotherpolicy[bindings j[a]] e[b scene[k jgpolicytruth[v bindings v scene]]].
d jgexercise[bindings j[a]] e[b scene[k jgexercisetruth[v bindings v scene]]].
d jgotherexercise[bindings j[a]] e[b scene[k jgexercisetruth[v bindings v scene]]].
'''
REFS = {n: 'k jg' + n + '[]' for n in (*CONSTANTS, 'start', 'end', 'status', 'polarity', 'bindings', 'exercisebindings')}
REFS.update({n: 'p jg' + n for n in ('valid', 'exercisevalid', 'controlled', 'performed', 'recognizes', 'realized', 'relation')})
REFS.update(target='r[p jgpolicy]', exercise='r[p jgexercise]')


def setup(text, source=False):
    if source:
        queries = ['q[t[' + k(name, *(REFS[n] for n, _ in fields)) + '][k jgstart[]]].' for name, fields in
            (('hzc2', SOURCE), ('hzc3', SOURCE), ('hzc4', PERMITTED))]
    else:
        queries = ['q[' + k(name, *(REFS[n] for n, _ in fields)) + '].' for name, fields in
            (('riv', EFFECT), ('riw', TRANSITION), ('rix', POWER), ('riy', ACTUAL))]
    return candidate(text, EXTRA + ''.join(queries))


def model_for(doc, prior=False, subsequent=True, status=True, polarity=True, controlled=True, recognized=True,
        performed=False, realized=False, permission=True, forbidden=False, permission_effect=True, variant='baseline', source=False):
    model = guarded(doc)
    model.update({'jg' + n: (lambda value=value: value) for n, value in CONSTANTS.items()})
    exercise_args = ('other', 'capacity') if variant == 'wrong_owner' else ('holder', 'capacity', 'other') if variant == 'bad_exercise_shape' else ('holder', 'capacity')
    target_args = ('beneficiary', 'role', 'other') if variant == 'bad_target_shape' else ('beneficiary', 'role')
    ex_syntax = syntax(quoted('function_ref', 'jgotherexercise' if variant == 'exercise_alias' else 'jgexercise'))
    target_syntax = syntax(quoted('function_ref', 'jgotherpolicy' if variant == 'target_alias' else 'jgpolicy'))
    endpoint = 'alternative' if variant in ('alternative', 'split_result') else 'after'
    changed_endpoint = 'alternative' if variant == 'alternative' else 'after'
    def controlled_record(actor, description, bindings, scene):
        expected_actor = 'other' if variant == 'wrong_actor' else 'holder'
        return (actor, description.syntax, bindings.items, scene) == (expected_actor, ex_syntax, exercise_args, 'before')
    def recognizes(framework, actor, capacity, description, bindings, start, end):
        expected = ('other' if variant == 'wrong_framework' else 'framework', 'holder', 'other' if variant == 'wrong_capacity' else 'capacity', ex_syntax, exercise_args, 'before', endpoint)
        return recognized and (framework, actor, capacity, description.syntax, bindings.items, start, end) == expected
    def effect(source_, person, role, description, bindings, sign, scene, after):
        expected = ('other' if variant == 'wrong_source' else 'contract', 'other' if variant == 'wrong_person' else 'beneficiary',
            'other' if variant == 'wrong_role' else 'role', target_syntax,
            tuple(reversed(target_args)) if variant == 'wrong_bindings' else target_args, not polarity if variant == 'wrong_polarity' else polarity)
        if (source_, person, role, description.syntax, bindings.items, sign) != expected: return False
        return prior if scene == 'before' else after if scene == changed_endpoint else False
    def exercise_norm(args, sign):
        assessor, actor, capacity, description, bindings, polarity_, scene = args
        return (assessor, actor, capacity, description.syntax, bindings.items, polarity_, scene) == ('assessor', 'holder', 'capacity', syntax(quoted('function_ref', 'jgexercise')), exercise_args, sign, 'before')
    model.update(jgstart=lambda: 'before', jgend=lambda: 'before' if variant == 'same_state' else 'after',
        jgstatus=lambda: status, jgpolarity=lambda: polarity, jgbindings=lambda: seq(target_args), jgexercisebindings=lambda: seq(exercise_args),
        jgvalid=lambda bindings: len(bindings.items) == 2, jgexercisevalid=lambda bindings: len(bindings.items) == 2,
        jgcontrolled=lambda *a: controlled and controlled_record(*a), jgrecognizes=recognizes,
        jgperformed=lambda a, d, b, c: performed and controlled_record(a, d, b, 'before' if variant == 'split_execution' and c == 'alternative' else c) and (variant != 'split_execution' or c == 'alternative'),
        jgrealized=lambda start, end: realized and (start, end) == ('before', 'alternative' if variant == 'split_realized' else endpoint),
        jgrelation=lambda *a: effect(*a, subsequent))
    if source:
        model.update(h7k=lambda *a: effect(*a, subsequent) or forbidden and exercise_norm(a, False),
            h7l=lambda *a: effect(*a, permission_effect) or permission and exercise_norm(a, True))
    return model


def evaluate(doc, model): return values(doc, model, DOMAIN, SCENES)


def generic_checks(texts):
    docs = [setup(t) for t in texts]; cases = []
    for prior, subsequent, status, controlled, recognized in product((False, True), repeat=5):
        changed = prior != status and subsequent == status
        want = [changed, changed and controlled and recognized, changed and controlled and recognized, False]
        rows = [evaluate(d, model_for(d, prior, subsequent, status, controlled=controlled, recognized=recognized)) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Norm transition, control and recognition conflated')
        cases.append(dict(prior=prior, subsequent=subsequent, status=status, controlled=controlled, recognized=recognized, results=want))
    polarity_cases = []
    for polarity, status in product((False, True), repeat=2):
        rows = [evaluate(d, model_for(d, prior=not status, subsequent=status, status=status, polarity=polarity)) for d in docs]
        if rows != [[True, True, True, False]] * len(docs): raise ValueError('Repeal confused with negative content')
        polarity_cases.append(dict(polarity=polarity, status=status, results=rows[0]))
    contrasts = {}
    for variant in ('exercise_alias', 'target_alias', 'wrong_owner', 'bad_exercise_shape', 'bad_target_shape', 'wrong_actor',
        'wrong_framework', 'wrong_capacity', 'wrong_source', 'wrong_person', 'wrong_role', 'wrong_bindings', 'wrong_polarity',
        'same_state', 'alternative', 'split_result', 'split_execution', 'split_realized'):
        if variant in ('target_alias', 'bad_target_shape', 'wrong_source', 'wrong_person', 'wrong_role', 'wrong_bindings', 'wrong_polarity'): want = [False] * 4
        elif variant in ('same_state', 'alternative'): want = [False, False, True, False]
        elif variant in ('split_execution', 'split_realized'): want = [True, True, True, False]
        else: want = [True, False, False, False]
        rows = [evaluate(d, model_for(d, variant=variant, performed=True, realized=True)) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Normative power contrast ' + variant + ': ' + repr(rows))
        contrasts[variant] = want
    actual_cases = []
    for recognized, performed, realized in product((False, True), repeat=3):
        want = [True, recognized, recognized, recognized and performed and realized]
        rows = [evaluate(d, model_for(d, recognized=recognized, performed=performed, realized=realized)) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Power became actual exercise')
        actual_cases.append(dict(recognized=recognized, performed=performed, realized=realized, results=want))
    for d in docs:
        for name in ('jgrelation', 'jgcontrolled', 'jgrecognizes', 'jgvalid', 'jgexercisevalid'):
            model = model_for(d); model[name] = guarded(d)[name]
            try: evaluate(d, model)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc): raise
            else: raise ValueError('Unknown norm/power relation guessed')
        model = model_for(d); model['jgperformed'] = guarded(d)['jgperformed']; model['jgrealized'] = guarded(d)['jgrealized']
        power = deepcopy(d); power['statements'] = power['statements'][:3]
        if evaluate(power, model) != [True] * 3: raise ValueError('Power needs actual exercise')
    return dict(cases=cases, polarity_cases=polarity_cases, contrasts=contrasts, actual_cases=actual_cases,
        standalone_agrees=True, policy_truth_not_executed=True, unknown_relations_refused=True, unknown_actuality_does_not_block_power=True)


def source_checks(texts):
    docs = [setup(t, True) for t in texts]; cases = []
    for controlled, recognized, permission, forbidden, permission_effect in product((False, True), repeat=5):
        power = controlled and recognized
        want = [power, power and permission_effect, power and permission and not forbidden]
        rows = [evaluate(d, model_for(d, controlled=controlled, recognized=recognized, permission=permission, forbidden=forbidden,
            permission_effect=permission_effect, source=True)) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Permission, requirement power and permission power conflated')
        cases.append(dict(controlled=controlled, recognized=recognized, permission=permission, forbidden=forbidden,
            permission_effect=permission_effect, results=want))
    return dict(cases=cases, standalone_agrees=True, permission_independent_of_power=True, requirement_and_permission_effects_distinct=True)


def quoted_checks(texts):
    for text in texts:
        doc = setup(text, True); doc['statements'] = []
        refs = [REFS[n] for n, _ in SOURCE] + ['u[' + TRUE + ']']
        probes = parse(format_graph(doc, 'compact') + ''.join('q[e[r[' + ref + ']][r[' + ref + ']]].' for ref in refs))
        closed = [q['body']['arguments'][0] for q in probes['statements']]
        base = apply_description(doc, quoted('function_ref', 'hzc2'), closed[:-1])
        question = apply_description(doc, quoted('function_ref', 'rij'), [base, closed[-1]])
        answer = apply_description(doc, quoted('function_ref', 'rii'), [base, closed[-1]])
        arguments = [quoted('call', 'jg' + n)['body'] for n in ('first', 'second', 'author', 'start')] + [question, answer]
        doc['statements'] = [dict(kind='ask', body=dict(kind='call', symbol='hzcu', arguments=arguments))]
        model = guarded(doc)
        model.update(jgfirst=lambda: 'first', jgsecond=lambda: 'second', jgauthor=lambda: 'author', jgstart=lambda: 'before',
            hzcr=lambda n, a, q, c: (n, a, q.syntax, c) == ('first', 'author', syntax(question), 'before'),
            uc=lambda n, a, r, c: (n, a, r.syntax, c) == ('second', 'author', syntax(answer), 'before'),
            ue=lambda x, y, c: (x, y, c) == ('first', 'second', 'before'),
            hzcs=lambda a, x, y, c: (a, x, y, c) == ('author', 'first', 'second', 'before'))
        if evaluate(doc, model) != [True]: raise ValueError('Quoted question executed or guessed normative power')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Quoted power roundtrip differs')
    return dict(shared_negative_base=True, unknown_power_not_evaluated=True, roundtrips=True)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Stored normative power differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Normative power roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = dict(characters=len(text), statements=len(doc['statements']))
    doc, parent = parse(texts[1]), parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']: raise ValueError('Parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0013')
    phrase = 'berechtigt sein'; start = unit['text'].index(phrase)
    if unit['text'].count(phrase) != 1: raise ValueError('Ambiguous source phrase')
    segment = dict(unit=unit['id'], unit_sha256=unit['text_sha256'], status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase, definitions=['rix', 'hzc2', 'hzc3', 'hzc4'])
    paths = [*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_normative_powers.py', 'scripts/check_normative_powers.py', 'scripts/check_closed_policies.py', 'scripts/check_policy_norms.py',
        'scripts/check_conditional_release.py', 'scripts/check_described_appraisals.py', 'scripts/check_public_assessment.py', 'scripts/check_rod_setup.py',
        'noema/finite_semantics.py', 'noema/extraction.py', 'noema/description_templates.py', 'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_normative_power_interpretation', documents=documents, sizes=sizes,
        generic=generic_checks([texts[0], texts[2]]), source=source_checks(texts[1:]), quoted=quoted_checks(texts[1:]),
        alignment=dict(segments=[segment], semantic_completion=False), new_definitions=7, new_primitives=0, new_author_statements=0,
        parent_preserved=True, roundtrips=True, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        interpretive_reference='https://persweb.wabash.edu/facstaff/helmang/phi213-1314S/phi213-txtbrwsr/Hohfeld/Hohfeld1913.html',
        source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in paths})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); options = parser.parse_args()
    report = build_report()
    if options.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Normative power report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream: json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Norm creation/repeal, controlled constitutive change, permission and actual exercise checked')


if __name__ == '__main__': main()
