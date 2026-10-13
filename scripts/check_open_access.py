"""Check scope-wide admission separately from usable methods and readership."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_rod_setup import guarded
from scripts.compose_open_access import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/open-access-v1.json'
DOMAIN = ('a', 'b', 'p', 'q', 'authority', 'channel', 'topic', 'acta', 'actb')
SCENES = ('now', 'good', 'bad')
EXTRA = '''r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[] d.
r zf[a a a a a i[h[a] f] d] c.r zg[a a a a a i[h[a] f] d] c.
r zh[a a d] c.r zi[a a d d] c.r zj[a a d d] c.r zk[a] e.r zl[a] c.r zm[a d] c.
d zn[person a] f[j s[b scene[k zm[v person v scene]]]].
d zo[person a] f[j q[b scene[k zm[v person v scene]]]].
'''
BASE = 'k za[] k zb[] k zc[] k zd[] r[p zn] k ze[] p zf p zg'
SCOPED = 'p zl k za[] k zc[] k zd[] r[p zn] k ze[] p zf p zg'
SOURCE = 'k za[] k zc[] k zd[] r[p zn] k ze[]'


def forbidden(*args):
    raise ValueError('Access evaluated the message truth or understanding')


def generic_checks():
    doc = candidate(generic_composed()[0], EXTRA + 'q[k rdh[' + BASE + ']].q[k rdj[' + BASE + ' k zk[k zb[]] p zh p zi p zj]].')
    accepted = 0
    for flags in product((False, True), repeat=9):
        grant, deny, available, good_outcome, bad_outcome, select_good, select_bad, good_success, bad_success = flags
        method = lambda person, plan, start: (person, plan, start) == ('a', 'p', 'now')
        bound = lambda authority, person, plan, channel, subject, desc, start: (
            authority, person, plan, channel, subject, symbol(desc), start) == ('authority', 'a', 'p', 'channel', 'topic', 'zn', 'now')
        model = guarded(doc)
        model.update(za=lambda: 'authority', zb=lambda: 'a', zc=lambda: 'channel', zd=lambda: 'topic', ze=lambda: 'now',
            zf=lambda *args: grant and bound(*args), zg=lambda *args: deny and bound(*args),
            zh=lambda *args: available and method(*args),
            zi=lambda person, plan, start, end: method(person, plan, start) and (
                end == 'good' and good_outcome or end == 'bad' and bad_outcome),
            zj=lambda person, plan, start, end: method(person, plan, start) and (
                end == 'good' and select_good or end == 'bad' and select_bad),
            zk=lambda person: Content(SCENES, (False, good_success, bad_success)), zm=forbidden)
        actual = values(doc, model, DOMAIN, SCENES)
        valid = (select_good or select_bad) and (not select_good or good_outcome) and (not select_bad or bad_outcome)
        success = (not select_good or good_success) and (not select_bad or bad_success)
        expected = [grant and not deny, grant and not deny and available and valid and success]
        if actual != expected:
            raise ValueError('Permission, assessment and access collapsed: ' + str((flags, actual)))
        accepted += actual[1]
    return {'method_state_cases': 512, 'accepted_access_cases': accepted,
        'message_truth_not_evaluated': True}


def source_model(doc, variant='baseline'):
    people = ('a', 'b')
    plans = {'a': 'p', 'b': 'q'}
    def scope(person, start):
        return variant != 'empty_scope' and person in people and start == 'now' and not (
            variant == 'narrowed_to_invited' and person == 'b')
    def rule(authority, person, plan, channel, subject, desc, start):
        expected_plan = 'p' if variant == 'split_method' and person == 'b' else plans.get(person)
        return person in people and (authority, plan, channel, subject, symbol(desc), start) == (
            'topic' if variant == 'wrong_authority' else 'authority', expected_plan,
            'topic' if variant == 'wrong_permission_channel' else 'channel',
            'channel' if variant == 'wrong_permission_subject' else 'topic',
            'zo' if variant == 'wrong_permission_description' else 'zn',
            'bad' if variant == 'wrong_permission_time' else 'now')
    def granted(*args):
        return variant not in ('no_permission', 'actual_without_permission') and not (
            variant in ('invited_only', 'narrowed_to_invited') and args[1] == 'b') and rule(*args)
    def denied(*args):
        if variant == 'other_authority_denies':
            return args[0] == 'topic' and rule('authority', *args[1:])
        return variant == 'conflicting_rule' and rule(*args)
    def available(person, plan, start):
        return variant != 'no_means' and not (variant == 'one_person_without_means' and person == 'b') and (
            person in people and (plan, start) == (plans[person], 'now'))
    def outcomes(person, plan, start, end):
        return person in people and (plan, start) == (plans[person], 'now') and (
            end == 'good' and variant != 'no_outcomes' or end == 'bad' and variant in ('lucky_outcome_only', 'unselected_failure'))
    def selected(person, plan, start, end):
        return variant != 'empty_selection' and person in people and (plan, start) == (plans[person], 'now') and (
            end == 'good' or end == 'bad' and variant in ('lucky_outcome_only', 'selection_outside_outcomes'))
    def receipt(act, person, subject, desc, end):
        actual = variant in ('actual_receipt', 'actual_without_permission')
        expected_act = {'a': 'acta', 'b': 'actb'}.get(person)
        return person in people and (act, subject, symbol(desc)) == (expected_act,
            'channel' if variant == 'wrong_received_subject' else 'topic',
            'zo' if variant == 'wrong_received_description' else 'zn') and (
            end == 'good' or actual and person == 'a' and end == 'now')
    model = guarded(doc)
    model.update(za=lambda: 'authority', zb=lambda: 'a', zc=lambda: 'channel', zd=lambda: 'topic', ze=lambda: 'now',
        zf=granted, zg=denied, zh=available, zi=outcomes, zj=selected,
        zl=lambda person: scope(person, 'now'), zm=forbidden,
        aa=lambda person: person in people, ae=available, af=outcomes, ap=selected,
        h6l=granted, h6m=denied, h6n=scope,
        dg=lambda act, end: act in ('acta', 'actb') and (end == 'good' or variant in (
            'actual_receipt', 'actual_without_permission') and (act, end) == ('acta', 'now')),
        h6k=lambda act, channel, end: act in ('acta', 'actb') and channel == (
            'topic' if variant == 'wrong_receipt_channel' else 'channel'), h6e=receipt)
    return model


def source_checks():
    text = source_composed()[0]
    doc = candidate(text, EXTRA + 'q[k h6q[' + SOURCE + ']].q[k h6r[' + SOURCE + ''']].
q[k h6s[k zb[] k zc[] k zd[] r[p zn] k ze[]]].''')
    rows = {}
    variants = ('baseline', 'actual_receipt', 'actual_without_permission', 'invited_only', 'no_permission',
        'conflicting_rule', 'other_authority_denies', 'no_means', 'one_person_without_means', 'split_method',
        'no_outcomes', 'empty_selection', 'selection_outside_outcomes', 'lucky_outcome_only', 'unselected_failure',
        'wrong_authority', 'wrong_permission_channel', 'wrong_permission_subject', 'wrong_permission_description',
        'wrong_permission_time', 'wrong_receipt_channel', 'wrong_received_subject', 'wrong_received_description', 'empty_scope',
        'narrowed_to_invited')
    no_admission = {'actual_without_permission', 'invited_only', 'no_permission', 'conflicting_rule', 'wrong_authority',
        'wrong_permission_channel', 'wrong_permission_subject', 'wrong_permission_description', 'wrong_permission_time', 'empty_scope'}
    usable = {'baseline', 'actual_receipt', 'other_authority_denies', 'unselected_failure', 'narrowed_to_invited'}
    for variant in variants:
        actual = values(doc, source_model(doc, variant), DOMAIN, SCENES)
        expected = [variant not in no_admission, variant in usable, variant in ('actual_receipt', 'actual_without_permission')]
        if actual != expected:
            raise ValueError('Native access contrast differs: ' + str((variant, actual)))
        rows[variant] = actual
    admission = candidate(text, EXTRA + 'q[k h6q[' + SOURCE + ']].')
    model = source_model(admission)
    for name in ('ae', 'af', 'ap', 'dg', 'h6e', 'h6k', 'h6g'):
        model[name] = forbidden
    if values(admission, model, DOMAIN, SCENES) != [True]:
        raise ValueError('Admission required ability or actual receipt')
    def unknown(*args):
        raise ValueError('Unassessed access rule')
    model['h6l'] = unknown
    try:
        values(admission, model, DOMAIN, SCENES)
    except ValueError as exc:
        if 'Unassessed access rule' not in str(exc):
            raise
    else:
        raise ValueError('Unknown permission treated as absence')
    return {'cases': rows, 'admission_does_not_evaluate_methods_receipt_or_understanding': True,
        'unassessed_permission_refused': True, 'same_scope_used_for_admission_and_usable_access': True,
        'independence_and_adequacy_of_audience_remain_a_caller_contract': True}


def alignment():
    path = ROOT / 'artifacts/written-units-v1/kant-1784.json'
    manifest = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['works']['kant-1784']['units_sha256']:
        raise ValueError('Source inventory changed')
    unit = next(row for row in json.loads(path.read_text(encoding='utf-8'))['units'] if row['id'] == 'kant-1784:u0012')
    text = unit['text']
    if hashlib.sha256(text.encode()).hexdigest() != unit['text_sha256']:
        raise ValueError('Source unit changed')
    source = 'vor dem ganzen Publikum der Leserwelt'
    start = text.index(source)
    return {'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'start': start, 'end': start + len(source),
        'source': source, 'definitions': ['h6o', 'h6p', 'h6q', 'h6r', 'h6s'], 'status': 'partial_explicit_reading',
        'full_semantic_equivalence': False, 'remaining': ['reader world and normative sources',
            'public address versus access rules', 'scholarly role and independent reasoning',
            'participation and response', 'integration with the older public/private draft and source equivalence']}


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'open-access'), (source_composed, 'kant-open-access')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored access conditions differ')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Access roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Earlier source changed')
    paths = list(documents) + [PARENT, 'data/open-access-basis-v1.json', 'data/kant-open-access-basis-v1.json',
        'scripts/compose_open_access.py', 'scripts/check_open_access.py', 'noema/discourse.py', 'noema/finite_semantics.py',
        'artifacts/written-units-v1/kant-1784.json', 'reports/written-units-v1.json']
    return json.loads(json.dumps({'status': 'partial_admission_and_access_not_full_public_reason',
        'documents': documents, 'generic': generic_checks(), 'source_cases': source_checks(), 'alignment': alignment(),
        'roundtrips': True, 'parent_preserved': True, 'new_source_assertions': 0,
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
            raise ValueError('Access report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Admission, same-method access and actual receipt checked independently')


if __name__ == '__main__':
    main()
