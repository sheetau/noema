"""Check higher-order protection without assuming compliance or permission."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.policy_descriptions import close_policy_description
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_closed_policies import quoted
from scripts import check_office_speech as office
from scripts.compose_protected_speech import ROOT, PARENT, source_composed

REPORT = ROOT / 'reports/protected-speech-v1.json'
EXTRA = office.EXTRA + '''r zp[] a.r zq[] a.
d zr[regulator a person a role a activity a] e[k hzq[v regulator v person v role v activity]].
'''


def setup():
    base = candidate(source_composed()[0], EXTRA)
    args = [quoted('call', s) for s in ('zj', 'za', 'zf', 'ze')]
    target = close_policy_description(base, quoted('function_ref', 'hzq'), args)
    return base, target, args


def queries(base, target):
    fields = [quoted('call', name)['body'] for name in ('zp', 'zj', 'zq')]
    context = quoted('call', 'zk')['body']
    statements = [{'kind': 'ask', 'body': {'kind': 'call', 'symbol': name,
        'arguments': [*fields, target, context]}} for name in ('hzr', 'hzs', 'hzt')]
    statements += [{'kind': 'ask', 'body': {'kind': 'call', 'symbol': 'hzc', 'arguments': [target, context]}}]
    # Separate public classification from actual permission and performance.
    suffix = ('q[k h6v[k za[] k ze[] k zf[] k zg[] k zh[] k zi[] r[p zm] k zk[]]].'
        'q[k h7c[' + office.PUBLIC + ']].q[k hzp[' + office.DUTY + ']].'
        'q[t[k zzq[k za[] k ze[]]][k zk[]]].')
    return parse(format_graph({**base, 'statements': statements}, 'compact') + suffix)


def model_for(doc, target, bits=(True, False, False, False, False), variant='baseline'):
    protected, opposed, banned, allowed, performed = bits
    model = office.model_for(doc, (True, allowed, banned, False, performed))
    syntax = json.dumps(target['body'], sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    def required(source, regulator, role, description, bindings, sign, context):
        expected = ['assessor', 'authority', 'regulating_role', 'now']
        for i, field in enumerate(('outer_source', 'outer_regulator', 'outer_role', 'outer_context')):
            if variant == field:
                expected[i] = 'elsewhere' if i == 3 else 'other'
        return [source, regulator, role, context] == expected and description.syntax == syntax and bindings.items == () and (
            opposed if sign else protected)
    model.update(zp=lambda: 'assessor', zq=lambda: 'regulating_role', h7k=required)
    # No upper-level permission is consulted by a requirement query.
    return model


def finite_checks():
    base, target, args = setup()
    doc = queries(base, target)
    domain = (*office.DOMAIN, 'assessor', 'regulating_role')
    rows = []
    for bits in product((False, True), repeat=5):
        protected, opposed, banned, allowed, performed = bits
        actual = values(doc, model_for(doc, target, bits), domain, office.SCENES)
        expected = [protected, protected and not opposed, protected and banned, banned,
                    True, allowed and not banned, True, performed]
        if actual != expected:
            raise ValueError('Protection, compliance and permission collapsed: ' + str((bits, actual)))
        rows.append({'states': list(bits), 'results': actual})
    contrasts = {}
    for variant in ('outer_source', 'outer_regulator', 'outer_role', 'outer_context'):
        actual = values(doc, model_for(doc, target, (True, False, True, False, False), variant), domain, office.SCENES)
        if actual != [False, False, False, True, True, False, True, False]:
            raise ValueError('Upper norm binding differs: ' + variant)
        contrasts[variant] = actual
    for field, index in (('inner_regulator', 0), ('inner_person', 1), ('inner_role', 2), ('inner_activity', 3)):
        changed_args = deepcopy(args)
        changed_args[index] = quoted('call', 'zb')
        changed = close_policy_description(base, quoted('function_ref', 'hzq'), changed_args)
        altered = queries(base, changed)
        # Keep the original protected target in the normative interpretation.
        actual = values(altered, model_for(altered, target, (True, False, True, False, False)), domain, office.SCENES)
        if actual != [False, False, False, False, True, False, True, False]:
            raise ValueError('Inner target identity collapsed: ' + field)
        contrasts[field] = actual
    alias = close_policy_description(base, quoted('function_ref', 'zr'), args)
    alias_doc = queries(base, alias)
    actual = values(alias_doc, model_for(alias_doc, target, (True, False, True, False, False)), domain, office.SCENES)
    if actual != [False, False, False, True, True, False, True, False]:
        raise ValueError('Coextensive policy descriptions inherited protection')
    contrasts['equivalent_alias'] = actual
    # The state of the ban can be unknown while a higher-order norm is known.
    norms = {**doc, 'statements': doc['statements'][:2]}
    model = model_for(norms, target)
    for name in ('h7a', 'h7b', 'cg', 'ca', 'cb', 'cf', 'h6u'):
        model[name] = guarded(norms)[name]
    if values(norms, model, domain, office.SCENES) != [True, True]:
        raise ValueError('Protection demanded knowledge of its fulfillment')
    for name, selected in (('h7a', {**doc, 'statements': doc['statements'][:3]}), ('h7k', norms)):
        missing = model_for(selected, target)
        missing[name] = guarded(selected)[name]
        try:
            values(selected, missing, domain, office.SCENES)
        except ValueError as exc:
            if 'Unrelated primitive' not in str(exc):
                raise
        else:
            raise ValueError('Unknown prohibition or protection silently became false')
    # Violation is about the ban's existence, not the protected person's action.
    violation = {**doc, 'statements': doc['statements'][:4]}
    model = model_for(violation, target, (True, False, True, False, False))
    for name in ('h7b', 'cg'):
        model[name] = guarded(violation)[name]
    if values(violation, model, domain, office.SCENES) != [True, True, True, True]:
        raise ValueError('Violation was inferred from the citizen remaining silent')
    # A second complete normative profile: a valid protection with a ban that
    # is in place elsewhere does not violate the present-context requirement.
    elsewhere = model_for(doc, target)
    original = elsewhere['h7a']
    elsewhere['h7a'] = lambda source, person, role, activity, desc, sign, context: original(
        source, person, role, activity, desc, sign, context) or (
        (source, person, role, activity, sign, context) == ('authority', 'person', 'scholar', 'speech', False, 'elsewhere'))
    actual = values(doc, elsewhere, domain, office.SCENES)
    if actual != [True, True, False, False, True, False, True, False]:
        raise ValueError('Ban in another context contaminated present violation')
    contrasts['ban_elsewhere'] = actual
    return {'state_cases': rows, 'binding_contrasts': contrasts,
        'closed_ban_target': target, 'norms_without_fulfillment_assessment': True,
        'unknown_norms_and_bans_refused': True, 'violation_without_speech_assessment': True,
        'public_classification_and_office_obligation_preserved': True}


def alignment():
    row = deepcopy(json.loads((ROOT / 'reports/office-speech-v1.json').read_text(encoding='utf-8'))['alignment']['segments'][0])
    row['definitions'] = ['hzq', 'hzr', 'hzs', 'hzt']
    row['review_ja'] = '現状の許可とは別に、指定された禁止状態を成立させてはならないという上位の要求を記述する。規範に反する禁止も表現できる。評価規範の公正さ・正当性、軍務・欠陥・判断への提出の全意味は未確認。'
    return {'segments': [row], 'new_source_ranges': False, 'semantic_completion': False}


def build_report():
    text, basis = source_composed()
    doc = parse(text)
    if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
            (ROOT / 'data/kant-protected-speech-basis-v1.json').read_text(encoding='utf-8')) != basis:
        raise ValueError('Stored protected speech differs')
    for notation in ('compact', 'full'):
        form = format_graph(doc, notation)
        if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
            raise ValueError('Protected speech roundtrip differs')
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Parent changed')
    paths = [basis['document'], PARENT, 'data/kant-protected-speech-basis-v1.json',
        'scripts/compose_protected_speech.py', 'scripts/check_protected_speech.py', 'scripts/check_office_speech.py',
        'scripts/check_closed_policies.py', 'reports/office-speech-v1.json',
        'noema/policy_descriptions.py', 'noema/description_templates.py', 'noema/finite_semantics.py', 'noema/discourse.py']
    return json.loads(json.dumps({'status': 'partial_prohibition_of_ban_not_general_justification',
        'documents': {basis['document']: audit_basis(doc, basis)}, 'finite': finite_checks(), 'alignment': alignment(),
        'roundtrips': True, 'parent_preserved': True, 'new_primitives': 0, 'new_source_assertions': 0,
        'notation_size': {'canonical_source_document_characters': len(text),
            'added_characters': len(text) - len((ROOT / PARENT).read_text(encoding='utf-8'))},
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}, ensure_ascii=False))


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Protected speech report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Protection against prohibition checked separately from permission and performance')


if __name__ == '__main__':
    main()
