"""Check that a person's office duty does not consume their public speech role."""
import argparse
import hashlib
from itertools import product
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_rod_setup import guarded
from scripts.compose_office_speech import ROOT, PARENT, source_composed

REPORT = ROOT / 'reports/office-speech-v1.json'
EXTRA = '''
r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[] a.r zf[] a.r zg[] a.r zh[] a.
r zi[] a.r zj[] a.r zk[] d.
r zl[a d] c.d zm[subject a] f[j s[b scene[k zl[v subject v scene]]]].
d zn[subject a] f[j s[b scene[k zl[v subject v scene]]]].
d zo[person a activity a] e[k zzq[v person v activity]].
'''
DUTY = 'k za[] k zb[] k zc[] k zd[] k zk[]'
ARGS = 'k za[] k zb[] k zc[] k zd[] k ze[] k zf[] k zg[] k zh[] k zi[] r[p zm] k zj[] k zk[]'
PUBLIC = 'k za[] k ze[] k zf[] k zg[] k zh[] k zi[] r[p zm] k zk[] k zj[]'
QUERIES = ('q[k hzn[' + DUTY + ']].q[k h7c[' + PUBLIC + ']].q[k hzo[' + ARGS + ']].'
           'q[k hzp[' + DUTY + ']].q[t[k zzq[k za[] k ze[]]][k zk[]]].')
DOMAIN = ('person', 'duty', 'office', 'issuer', 'speech', 'scholar', 'audience',
          'channel', 'topic', 'authority', 'reader', 'other')
SCENES = ('now', 'elsewhere')


def model_for(doc, bits=(True, True, False, False, False), variant='baseline', rename=lambda s: s):
    required, allowed, forbidden, duty_done, speech_done = bits
    n = rename
    def matches(actual, expected, field=None):
        expected = list(expected)
        if variant == field:
            expected[-1] = 'elsewhere' if expected[-1] == 'now' else 'other'
        return tuple(actual) == tuple(n(x) for x in expected)
    def normative(source, person, role, activity, desc, sign, context):
        fields = [source, person, role, activity, context]
        expected = ['issuer', 'person', 'office', 'duty', 'now']
        for index, field in enumerate(('issuer', 'duty_person', 'duty_role', 'duty_activity', 'duty_context')):
            if variant == field:
                expected[index] = 'elsewhere' if index == 4 else 'other'
        duty_binding = fields == [n(x) for x in expected] and symbol(desc) == ('zo' if variant == 'duty_description' else 'zzq')
        public_binding = fields == [n(x) for x in ('authority', 'person', 'scholar', 'speech', 'now')] and symbol(desc) == 'zzq'
        return required and sign and duty_binding or forbidden and not sign and public_binding
    def permission(source, person, role, activity, desc, sign, context):
        expected = ['authority', 'person', 'scholar', 'speech', 'now']
        for index, field in enumerate(('authority', 'speech_person', 'speech_role', 'speech_activity', 'speech_context')):
            if variant == field:
                expected[index] = 'elsewhere' if index == 4 else 'other'
        return allowed and sign and [source, person, role, activity, context] == [n(x) for x in expected] and symbol(desc) == 'zzq'
    def publication(activity, channel, subject, desc, context):
        return matches((activity, channel, subject, context), ('speech', 'channel', 'topic', 'now')) and symbol(desc) == (
            'zn' if variant == 'message_description' else 'zm')
    def role(person, activity, office, context):
        return matches((person, activity, office, context), ('person', 'duty', 'office', 'now')) or matches(
            (person, activity, office, context), ('person', 'speech', 'office' if variant == 'speech_is_official' else 'scholar', 'now'))
    def execution(person, activity, context):
        return matches((person, context), ('person', 'now')) and (
            activity == n('duty') and duty_done or activity == n('speech') and speech_done)
    model = guarded(doc)
    model.update({key: (lambda value=value: n(value)) for key, value in zip(
        ('za', 'zb', 'zc', 'zd', 'ze', 'zf', 'zg', 'zh', 'zi', 'zj', 'zk'), (*DOMAIN[:10], 'now'))})
    model.update(h7a=normative, h7b=permission, cb=role,
        cf=lambda person, role, context: variant != 'no_entrusted_office' and matches((person, role, context), ('person', 'office', 'now')),
        ca=lambda person, activity, context: matches((person, activity, context), ('person', 'speech', 'now')),
        cc=lambda activity, audience, context: matches((activity, audience, context), ('speech', 'audience', 'now')),
        cd=lambda role, context: matches((role, context), ('scholar', 'now')),
        ce=lambda audience, context: variant != 'private_audience' and matches((audience, context), ('audience', 'now')),
        cg=execution, aa=lambda person: person in (n('person'), n('reader')),
        h6n=lambda person, context: matches((person, context), ('reader', 'now')),
        h6t=lambda audience, person, context: variant != 'missing_reader' and matches((audience, person, context), ('audience', 'reader', 'now')),
        h6u=publication)
    if variant == 'same_activity':
        model['ze'] = lambda: n('duty')
        # Permit and classify both targets, so the distinct-activity condition
        # itself, rather than a missing callback row, is exercised.
        for name, index in (('cb', 1), ('ca', 1), ('cc', 0), ('h6u', 0), ('h7b', 3)):
            original = model[name]
            def adapt(*args, original=original, index=index):
                alt = list(args)
                if alt[index] == n('duty'):
                    alt[index] = n('speech')
                return original(*args) or original(*alt)
            model[name] = adapt
    return model


def finite_checks():
    text, basis = source_composed()
    assert basis['role_linkage']['symbols']['roles']['cg'] == 'cg'
    doc = candidate(text, EXTRA + QUERIES)
    rows = []
    for bits in product((False, True), repeat=5):
        required, allowed, forbidden, duty_done, speech_done = bits
        actual = values(doc, model_for(doc, bits), DOMAIN, SCENES)
        permitted = allowed and not forbidden
        expected = [required, permitted, required and permitted, required and not duty_done, speech_done]
        if actual != expected:
            raise ValueError('Duty and public speech collapsed: ' + str((bits, actual)))
        rows.append({'states': list(bits), 'results': actual})
    contrasts = {}
    duty_mismatches = ('issuer', 'duty_person', 'duty_role', 'duty_activity', 'duty_context', 'duty_description', 'no_entrusted_office')
    speech_mismatches = ('authority', 'speech_person', 'speech_role', 'speech_activity', 'speech_context',
                         'speech_is_official', 'private_audience', 'missing_reader', 'message_description')
    for variant in (*duty_mismatches, *speech_mismatches, 'same_activity'):
        actual = values(doc, model_for(doc, variant=variant), DOMAIN, SCENES)
        expected = [False, True, False, False, False] if variant in duty_mismatches else (
            [True, True, False, True, False] if variant == 'same_activity' else [True, False, False, True, False])
        if actual != expected:
            raise ValueError('Role or target binding differs: ' + str((variant, actual)))
        contrasts[variant] = actual
    norms = {**doc, 'statements': doc['statements'][:3]}
    model = model_for(norms)
    model['cg'] = guarded(norms)['cg']
    if values(norms, model, DOMAIN, SCENES) != [True, True, True]:
        raise ValueError('Norms required actual execution')
    try:
        values(doc, model, DOMAIN, SCENES)
    except ValueError as exc:
        if 'Unrelated primitive' not in str(exc):
            raise
    else:
        raise ValueError('Unassessed performance became nonperformance')
    for name in ('h7a', 'h7b'):
        missing = model_for(norms)
        missing[name] = guarded(norms)[name]
        try:
            values(norms, missing, DOMAIN, SCENES)
        except ValueError as exc:
            if 'Unrelated primitive' not in str(exc):
                raise
        else:
            raise ValueError('Unknown norm became false')
    # Reinterpret the same formulas for a laboratory employee's assigned
    # procedure and separate public report. Names have no built-in semantics.
    renamed = lambda s: {'person': 'researcher', 'duty': 'procedure', 'office': 'laboratory_post',
        'issuer': 'lab_director', 'speech': 'public_report', 'scholar': 'independent_author'}.get(s, s)
    transferred = values(doc, model_for(doc, rename=renamed), tuple(map(renamed, DOMAIN)), SCENES)
    if transferred != [True, True, True, True, False]:
        raise ValueError('Nonmilitary interpretation differs')
    return {'state_cases': rows, 'binding_contrasts': contrasts, 'norms_do_not_evaluate_execution': True,
        'unknown_execution_and_norms_refused': True, 'laboratory_interpretation': transferred}


def alignment():
    path = ROOT / 'artifacts/written-units-v1/kant-1784.json'
    unit = next(u for u in json.loads(path.read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0012')
    excerpt = 'er muß gehorchen. Es kann ihm aber billigermaßen nicht verwehrt werden, als Gelehrter, über die Fehler im Kriegesdienste Anmerkungen zu machen, und diese seinem Publikum zur Beurtheilung vorzulegen.'
    if unit['text'].count(excerpt) != 1:
        raise ValueError('Source passage is not unique')
    start = unit['text'].index(excerpt)
    return {'segments': [{'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'status': 'partial',
        'range': [start, start + len(excerpt)], 'text': excerpt, 'definitions': ['hzn', 'hzo', 'hzp'],
        'review_ja': '同じ本人の職務上の実行要求と別の公的活動への許可を接続する部分草案。軍務・欠陥・判断への提出、禁止の不当性、直前の職務中の論評の害は未記述。許可の現状は原文の規範要求の代替ではない。'}],
        'new_source_ranges': True, 'semantic_completion': False}


def build_report():
    text, basis = source_composed()
    doc = parse(text)
    if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
            (ROOT / 'data/kant-office-speech-basis-v1.json').read_text(encoding='utf-8')) != basis:
        raise ValueError('Stored office/speech composition differs')
    for notation in ('compact', 'full'):
        form = format_graph(doc, notation)
        if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
            raise ValueError('Office/speech roundtrip differs')
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Parent changed')
    paths = [basis['document'], PARENT, 'data/kant-office-speech-basis-v1.json',
        'scripts/compose_office_speech.py', 'scripts/check_office_speech.py', 'scripts/check_conditional_release.py',
        'scripts/check_described_appraisals.py', 'scripts/check_described_explanations.py', 'scripts/check_rod_setup.py',
        'artifacts/written-units-v1/kant-1784.json', 'noema/finite_semantics.py', 'noema/discourse.py']
    return json.loads(json.dumps({'status': 'partial_office_duty_and_public_activity_binding',
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
            raise ValueError('Office/speech report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Office requirement, public permission and independent performance checked')


if __name__ == '__main__':
    main()
