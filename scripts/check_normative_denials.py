"""Distinguish guarded normative denials and bind them to a concrete undertaking."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.description_templates import apply_description
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_assessed_payments import description
from scripts.check_closed_policies import quoted
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_policy_norms import seq
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts import check_normative_powers as powers
from scripts import check_necessary_futures as futures
from scripts.compose_limits import call as k
from scripts.compose_normative_denials import ROOT, PARENT, BUILDERS, NORM, SOURCE, ADAPTER, POWER, POWER_SOURCE
from scripts.compose_successive_cohorts import UNDERTAKING

REPORT = ROOT / 'reports/normative-denials-v1.json'
EXTRA = powers.EXTRA + 'r jnrequired[' + powers.RULE[2:-3] + '] c.r jnallowed[' + powers.RULE[2:-3] + '] c.'
REFS = dict(source='k jgassessor[]', person='k jgactor[]', role='k jgcapacity[]', description='r[p jgexercise]',
    bindings='k jgexercisebindings[]', polarity='k jgpolarity[]', context='k jgstart[]', valid='p jgexercisevalid',
    required='p jnrequired', allowed='p jnallowed')


def norm_setup(text):
    return candidate(text, EXTRA + ''.join('q[' + k(n, *(REFS[x] for x, _ in NORM)) + '].' for n in ('rjp', 'rjq', 'rjr')))


def norm_model(doc, valid=True, permit=True, forbid=False, require=False, polarity=True):
    model = powers.model_for(doc, polarity=polarity)
    target = syntax(quoted('function_ref', 'jgexercise'))
    def bound(source, person, role, description, bindings, sign, context):
        return (source, person, role, description.syntax, bindings.items, context) == ('assessor', 'holder', 'capacity', target, ('holder', 'capacity'), 'before')
    model.update(jgexercisevalid=lambda b: valid and len(b.items) == 2,
        jnallowed=lambda *a: permit and a[-2] == polarity and bound(*a),
        jnrequired=lambda *a: bound(*a) and (require if a[-2] == polarity else forbid))
    return model


def generic_checks(texts):
    docs = [norm_setup(t) for t in texts]; cases = []
    for bits in product((False, True), repeat=5):
        valid, permit, forbid, require, polarity = bits
        want = [valid and not permit, valid and forbid, valid and (not permit or forbid)]
        rows = [powers.evaluate(d, norm_model(d, *bits)) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Permission absence, prohibition and conflict collapsed')
        cases.append(dict(bits=list(bits), results=want))
    for d in docs:
        for relation in ('jnallowed', 'jnrequired', 'jgexercisevalid'):
            model = norm_model(d); model[relation] = guarded(d)[relation]
            try: powers.evaluate(d, model)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc): raise
            else: raise ValueError('Unknown norm replaced with absence')
    power_docs = [candidate(t, powers.EXTRA + ''.join('q[' + k(n, *(powers.REFS[x] for x, _ in POWER)) + '].' for n in ('rjs', 'rix'))) for t in texts]
    power_cases = []
    for prior, subsequent, control, recognized in product((False, True), repeat=4):
        power = not prior and subsequent and control and recognized
        want = [not power, power]
        rows = [powers.evaluate(d, powers.model_for(d, prior=prior, subsequent=subsequent, controlled=control, recognized=recognized)) for d in power_docs]
        if rows != [want] * len(power_docs): raise ValueError('Guarded absence of power differs')
        power_cases.append(dict(prior=prior, subsequent=subsequent, controlled=control, recognized=recognized, results=want))
    invalid = {}
    for variant in ('wrong_owner', 'bad_exercise_shape', 'bad_target_shape'):
        rows = [powers.evaluate(d, powers.model_for(d, variant=variant)) for d in power_docs]
        if rows != [[False, False]] * len(power_docs): raise ValueError('Malformed power query became a denial')
        invalid[variant] = rows[0]
    for d in power_docs:
        for name in ('jgrelation', 'jgcontrolled', 'jgrecognizes', 'jgvalid', 'jgexercisevalid'):
            model = powers.model_for(d); model[name] = guarded(d)[name]
            try: powers.evaluate(d, model)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc): raise
            else: raise ValueError('Unknown power replaced with absence')
    return dict(cases=cases, power_cases=power_cases, invalid_power_inputs=invalid,
        standalone_agrees=True, unknown_relations_refused=True, underlying_policy_not_executed=True)


DOMAIN = tuple(dict.fromkeys((*futures.cohorts.DOMAIN, *powers.DOMAIN)))
SCENES = futures.cohorts.SCENES


def source_setup(text):
    original = futures.purpose_setup(text, 'hzdh')
    doc, goal, effect, trace = original
    bound = dict(zip((n for n, _ in UNDERTAKING), doc['statements'][1]['body']['arguments'], strict=True))
    doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + powers.EXTRA)
    target = apply_description(doc, quoted('function_ref', 'hzdk'), [dict(kind='quote', body=deepcopy(bound[n])) for n, _ in ADAPTER])
    references = REFS | dict(description='r[p jgexercise]')
    power_refs = powers.REFS | dict(source='k jc[]')
    queries = ''.join('q[t[' + k(n, *(references[x] for x, _ in SOURCE)) + '][k jgstart[]]].' for n in ('hzdl', 'hzdm', 'hzdn'))
    queries += ''.join('q[t[' + k(n, *(power_refs[x] for x, _ in POWER_SOURCE)) + '][k jgstart[]]].' for n in ('hzdo', 'hzdp', 'hzc2', 'hzc3'))
    doc = parse(format_graph(doc, 'compact') + queries)
    placeholder = quoted('function_ref', 'jgexercise')
    def replace(x):
        if isinstance(x, list): return [replace(y) for y in x]
        if not isinstance(x, dict): return x
        if x == placeholder: return deepcopy(target)
        return {n: replace(y) for n, y in x.items()}
    doc['statements'] = replace(doc['statements'])
    return parse(format_graph(doc, 'compact')), target, (doc, goal, effect, trace)


def source_model(setup, permit=True, forbid=False, control=True, recognized=True, permission_effect=True, variant='baseline'):
    doc, target, _ = setup
    model = powers.model_for(doc)
    exercise = syntax(target); policy = syntax(quoted('function_ref', 'jgpolicy'))
    owner = 'other' if variant == 'wrong_owner' else 'oldgroup'
    bindings = (owner, 'capacity') if variant == 'extra_binding' else () if variant == 'empty_binding' else (owner,)
    def exercise_norm(source, person, role, desc, arguments, sign, point):
        return (source, person, role, desc.syntax, arguments.items, point) == ('assessor', 'oldgroup', 'capacity', exercise, ('oldgroup',), 'now')
    def effect_norm(source, person, role, desc, arguments, sign, point):
        return (source, person, role, desc.syntax, arguments.items, sign, point) == ('pact', 'beneficiary', 'role', policy, ('beneficiary', 'role'), True, 'future')
    def recognizes(framework, actor, capacity, desc, arguments, start, end):
        return recognized and (framework, actor, capacity, desc.syntax, arguments.items, start, end) == (
            'framework', 'oldgroup', 'capacity', exercise, ('oldgroup',), 'now', 'future')
    model.update(jgactor=lambda: 'oldgroup', jgstart=lambda: 'now', jc=lambda: 'pact',
        jgexercisebindings=lambda: seq(bindings), jgexercisevalid=lambda b: len(b.items) == 1,
        jgcontrolled=lambda a, d, b, s: control and (a, d.syntax, b.items, s) == ('oldgroup', exercise, ('oldgroup',), 'now'),
        jgrecognizes=recognizes,
        h7k=lambda *a: effect_norm(*a) or forbid and not a[-2] and exercise_norm(*a),
        h7l=lambda *a: permission_effect and effect_norm(*a) or permit and a[-2] and exercise_norm(*a))
    if variant == 'other_agreement': model['jc'] = lambda: 'other'
    return model


def adapter_checks(setups):
    cases = {}
    for members in (('oldgroup',), ('newgroup',), (), ('oldgroup', 'newgroup')):
        want = [members == ('oldgroup',)]
        for doc, target, original in setups:
            trial = deepcopy(doc)
            applied = dict(kind='apply', function=deepcopy(target['body']), arguments=[dict(kind='call', symbol='jgexercisebindings', arguments=[])])
            trial['statements'] = [dict(kind='ask', body=dict(kind='evaluate', content=applied, situation=dict(kind='call', symbol='je', arguments=[])))]
            model = futures.cohorts.source_model((doc, *original[1:]))
            model['jgexercisebindings'] = lambda: seq(members)
            if values(trial, model, DOMAIN, SCENES) != want: raise ValueError('Undertaking adapter discarded its collective or extra bindings')
        cases[','.join(members) or 'empty'] = want
    return cases


def source_checks(texts):
    setups = [source_setup(t) for t in texts]; cases = []
    for bits in product((False, True), repeat=5):
        permit, forbid, control, recognized, permission_effect = bits
        power = control and recognized
        want = [not permit, forbid, not permit or forbid, not power, not (power and permission_effect), power, power and permission_effect]
        rows = [values(s[0], source_model(s, *bits), DOMAIN, SCENES) for s in setups]
        if rows != [want] * len(setups): raise ValueError('Concrete undertaking denial confused prohibition with power: ' + repr((bits, rows, want)))
        cases.append(dict(bits=list(bits), results=want))
    contrasts = {}
    for variant in ('wrong_owner', 'extra_binding', 'empty_binding', 'other_agreement'):
        want = [True, False, True, False, False, False, False] if variant == 'wrong_owner' else [False] * 7 if variant in ('extra_binding', 'empty_binding') else [False, False, False, True, True, False, False]
        rows = [values(s[0], source_model(s, variant=variant), DOMAIN, SCENES) for s in setups]
        if rows != [want] * len(setups): raise ValueError('Normative target contrast ' + variant + ': ' + repr(rows))
        contrasts[variant] = want
    for s in setups:
        doc = s[0]
        for relation in ('h7k', 'h7l', 'jgcontrolled', 'jgrecognizes'):
            model = source_model(s); model[relation] = guarded(doc)[relation]
            try: values(doc, model, DOMAIN, SCENES)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc): raise
            else: raise ValueError('Unknown normative denial inferred')
        # All ceremony, temporal, modal, epistemic and achieved-cause relations
        # remain guarded. The seven normative questions still have known values.
        if values(doc, source_model(s), DOMAIN, SCENES) != [False, False, False, False, False, True, True]: raise ValueError('Norm query executed its undertaking')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Closed normative denial changed')
    return dict(cases=cases, contrasts=contrasts, adapter=adapter_checks(setups), standalone_agrees=True,
        same_undertaking_for_norm_and_power=True, same_agreement_for_norm_effect=True,
        unknown_undertaking_not_executed=True, unknown_norms_refused=True, closed_roundtrips=True)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Stored normative denial differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Normative denial roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = dict(characters=len(text), statements=len(doc['statements']))
    doc, parent = parse(texts[1]), parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']: raise ValueError('Parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0013')
    phrase = 'kann sich nicht verbünden und darauf verschwören'
    if unit['text'].count(phrase) != 1: raise ValueError('Ambiguous source phrase')
    start = unit['text'].index(phrase)
    segment = dict(unit=unit['id'], unit_sha256=unit['text_sha256'], status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase, definitions=['hzdk', 'hzdl', 'hzdm', 'hzdn', 'hzdo', 'hzdp'])
    paths = [*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_normative_denials.py', 'scripts/check_normative_denials.py', 'scripts/check_normative_powers.py',
        'scripts/check_necessary_futures.py', 'scripts/check_successive_cohorts.py', 'scripts/check_assessed_payments.py',
        'scripts/check_closed_policies.py', 'scripts/check_conditional_release.py', 'scripts/check_policy_norms.py',
        'scripts/check_described_appraisals.py', 'scripts/check_public_assessment.py', 'scripts/check_rod_setup.py',
        'noema/finite_semantics.py', 'noema/extraction.py', 'noema/description_templates.py', 'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_guarded_normative_denials', documents=documents, sizes=sizes,
        generic=generic_checks([texts[0], texts[2]]), source=source_checks(texts[1:]),
        alignment=dict(segments=[segment], semantic_completion=False), new_definitions=10, new_primitives=0, new_author_statements=0,
        parent_preserved=True, roundtrips=True, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in paths})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); options = parser.parse_args()
    report = build_report()
    if options.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Normative denial report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream: json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Guarded normative denials and the same collective undertaking as norm and power target checked')


if __name__ == '__main__': main()
