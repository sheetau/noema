"""Verify old role projections, relocated semantics and publication bridges."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json
from unittest.mock import patch

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, number_word, parse
from noema.linking import project_document
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_rod_setup import guarded
from scripts import check_kant_roles as legacy
from scripts import check_open_access as access
from scripts.compose_public_use_link import ROOT, PARENT, ROLES, linkage, source_composed

REPORT = ROOT / 'reports/public-use-link-v1.json'


def projection_checks():
    linked, pairs = linkage()
    doc = parse(source_composed()[0])
    for label in pairs:
        projected = project_document(linked, label, document=doc)
        original = pairs[label][0]
        projected['schema_version'] = original['schema_version']
        projected['lexicon_version'] = original['lexicon_version']
        if parse(format_graph(projected, 'compact')) != original:
            raise ValueError('Complete source projection differs: ' + label)
    return {'both_complete_original_documents_recovered': True,
        'roles_edition_restored_to': pairs['roles'][0]['schema_version'],
        'independent_role_symbols': linked.symbols['roles'], 'shared_declarations': 0,
        'original_statement_count': len(pairs['current'][0]['statements'])}


def relocated_query(doc, name, args, primitives, individuals, situations, at=None):
    doc = deepcopy(doc)
    names = {row['name'] for row in doc['declarations']}
    body_args = []
    def constant(kind, value):
        index = 0
        while 'qq' + number_word(index) in names:
            index += 1
        name = 'qq' + number_word(index)
        names.add(name)
        doc['declarations'].append({'kind': 'primitive', 'name': name, 'parameters': [], 'result': kind})
        primitives[name] = lambda value=value: value
        return {'kind': 'call', 'symbol': name, 'arguments': []}
    for kind, value in args:
        body_args.append(constant(kind, value))
    body = {'kind': 'call', 'symbol': name, 'arguments': body_args}
    if at is not None:
        body = {'kind': 'evaluate', 'content': body, 'situation': constant('situation', at)}
    doc['statements'] = [{'kind': 'ask', 'body': body}]
    return evaluate_document(doc, individuals=individuals, situations=situations, primitives=primitives,
        max_steps=2_000_000, memoize_definitions=True, memoize_expressions=True)[0]['value']


def replay_checks():
    text, basis = source_composed()
    doc = parse(text)
    mapping = linkage()[0].symbols['roles']
    original_query = legacy.query
    count = 0
    def compare(original_doc, name, args, primitives, individuals, situations, at=None):
        nonlocal count
        old = original_query(original_doc, name, args, primitives, individuals, situations, at)
        moved = guarded(doc)
        moved.update({mapping[key]: value for key, value in primitives.items()})
        actual = relocated_query(doc, mapping[name], args, moved, individuals, situations, at)
        if actual != old:
            raise ValueError('Relocated role meaning changed: ' + name)
        count += 1
        return actual
    with patch.object(legacy, 'query', compare):
        norms, roles = legacy.normative_checks(), legacy.role_checks()
    with patch.object(access, 'source_composed', return_value=(text, basis)):
        current = access.source_checks()
    return {'normative_cases': norms, 'role_cases': roles, 'original_and_linked_evaluation_pairs': count,
        'current_access': current, 'legacy_modules_restored_after_replay': legacy.query is original_query}


def scope_checks():
    doc = candidate(source_composed()[0], 'r za[a] c.r zb[a] c.q[k rdl[p za p zb]].')
    count = 0
    for flags in product((False, True), repeat=4):
        left, right = dict(zip(('one', 'two'), flags[:2])), dict(zip(('one', 'two'), flags[2:]))
        model = guarded(doc)
        model.update(za=lambda person: left[person], zb=lambda person: right[person])
        expected = left == right and any(left.values())
        if values(doc, model, ('one', 'two'), ('now',)) != [expected]:
            raise ValueError('Nonempty audience equality differs')
        count += 1
    return count


def bridge_checks():
    mapping = linkage()[0].symbols['roles']
    args = 'k za[] k zb[] k zc[] k zd[] k ze[] k zf[] r[p zi] k zg[]'
    doc = candidate(source_composed()[0], '''r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[] a.r zf[] a.r zg[] d.r zh[] a.
r zj[a d] c.d zi[person a] f[j s[b scene[k zj[v person v scene]]]].
d zk[person a] f[j q[b scene[k zj[v person v scene]]]].
''' + 'q[k h6v[' + args + ']].q[k h6w[' + args + ' k zh[]]].q[k h6x[' + args + ' k zh[]]].q[k h6y[' + args + ' k zh[]]].'
        + 'q[t[k ' + mapping['dc'] + '[k za[] k zb[]]][k zg[]]].')
    domain = ('person', 'reader', 'role', 'activity', 'audience', 'otheraudience', 'channel', 'topic', 'authority', 'plan', 'receipt')
    scenes = ('now', 'received', 'performed')
    variants = ('baseline', 'actual_performance', 'reader_permission_only', 'writer_permission_only', 'no_reader_means',
        'writer_conflict', 'wrong_writer_role', 'not_reason_use', 'not_scholarly_role', 'wrong_activity_role',
        'other_public_audience', 'not_public_audience', 'missing_reader', 'extra_reader', 'empty_scopes',
        'wrong_activity_channel', 'wrong_activity_subject', 'wrong_activity_description', 'wrong_activity_context')
    rows = {}
    for variant in variants:
        performed = tuple(scene == 'performed' or variant == 'actual_performance' and scene == 'now' for scene in scenes)
        def recipient(person, context):
            return variant != 'empty_scopes' and (person, context) == ('reader', 'now')
        def audience_people(audience, person, context):
            return variant not in ('empty_scopes', 'missing_reader') and (audience, context) == ('audience', 'now') and (
                person == 'reader' or variant == 'extra_reader' and person == 'person')
        def publication(activity, channel, subject, desc, context):
            return (activity, channel, subject, symbol(desc), context) == ('activity',
                'topic' if variant == 'wrong_activity_channel' else 'channel',
                'channel' if variant == 'wrong_activity_subject' else 'topic',
                'zk' if variant == 'wrong_activity_description' else 'zi',
                'performed' if variant == 'wrong_activity_context' else 'now')
        def allowed(authority, person, plan, channel, subject, desc, context):
            return variant != 'writer_permission_only' and (authority, person, plan, channel, subject, symbol(desc), context) == (
                'authority', 'reader', 'plan', 'channel', 'topic', 'zi', 'now')
        def method(person, plan, start):
            return (person, plan, start) == ('reader', 'plan', 'now')
        model = guarded(doc)
        model.update(za=lambda: 'person', zb=lambda: 'activity', zc=lambda: 'role', zd=lambda: 'audience',
            ze=lambda: 'channel', zf=lambda: 'topic', zg=lambda: 'now', zh=lambda: 'authority',
            aa=lambda person: person in ('person', 'reader'), h6n=recipient, h6t=audience_people, h6u=publication,
            h6l=allowed, h6m=lambda *args: False,
            ae=lambda *args: variant != 'no_reader_means' and method(*args),
            af=lambda person, plan, start, end: method(person, plan, start) and end == 'received',
            ap=lambda person, plan, start, end: method(person, plan, start) and end == 'received',
            dg=lambda act, scene: (act, scene) == ('receipt', 'received'),
            h6k=lambda act, channel, scene: (act, channel, scene) == ('receipt', 'channel', 'received'),
            h6e=lambda act, person, subject, desc, scene: (act, person, subject, symbol(desc), scene) == ('receipt', 'reader', 'topic', 'zi', 'received'))
        old = {
            'aa': lambda authority, person, role, content, scene: variant == 'writer_conflict' and (
                authority, person, role, scene) == ('authority', 'person', 'role', 'now') and content.values == tuple(not x for x in performed),
            'ab': lambda authority, person, role, content, scene: variant != 'reader_permission_only' and (
                authority, person, role, scene) == ('authority', 'person', 'plan' if variant == 'wrong_writer_role' else 'role', 'now')
                and content.values == performed,
            'ca': lambda person, activity, scene: variant != 'not_reason_use' and (person, activity) == ('person', 'activity'),
            'cb': lambda person, activity, role, scene: variant != 'wrong_activity_role' and (person, activity, role) == ('person', 'activity', 'role'),
            'cc': lambda activity, audience, scene: (activity, audience) == ('activity', 'otheraudience' if variant == 'other_public_audience' else 'audience'),
            'cd': lambda role, scene: variant != 'not_scholarly_role' and role == 'role',
            'ce': lambda audience, scene: variant != 'not_public_audience' and audience in ('audience', 'otheraudience'),
            'cg': lambda person, activity, scene: (person, activity) == ('person', 'activity') and performed[scenes.index(scene)],
        }
        model.update({mapping[name]: value for name, value in old.items()})
        actual = values(doc, model, domain, scenes)
        public = variant in ('baseline', 'actual_performance', 'reader_permission_only', 'writer_permission_only',
            'no_reader_means', 'writer_conflict', 'wrong_writer_role')
        expected = [public, public and variant != 'writer_permission_only',
            public and variant not in ('writer_permission_only', 'no_reader_means'),
            public and variant not in ('reader_permission_only', 'writer_conflict', 'wrong_writer_role'), variant == 'actual_performance']
        if actual != expected:
            raise ValueError('Public-use bridge differs: ' + str((variant, actual)))
        rows[variant] = actual
    return {'cases': rows, 'message_truth_and_understanding_guarded': True,
        'public_classification_still_depends_on_legacy_conventions': True}


def alignment():
    mapping = linkage()[0].symbols['roles']
    data = json.loads((ROOT / 'data/kant-public-private-alignment-v1.json').read_text(encoding='utf-8'))
    source = json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    unit = next(row for row in source['units'] if row['id'] == data['source_unit'])
    if hashlib.sha256(unit['text'].encode()).hexdigest() != data['source_sha256']:
        raise ValueError('Role source alignment changed')
    rows = []
    for old in data['selections']:
        start = unit['text'].index(old['source'])
        row = {'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'start': start, 'end': start + len(old['source']),
            'source': old['source'], 'definitions': [mapping[name] for name in old['definitions']],
            'status': 'partial_explicit_reading', 'full_semantic_equivalence': False, 'review_ja': old['review_ja']}
        if old['id'] == 'definition-public-use':
            row['definitions'] += ['h6v', 'h6w', 'h6x', 'h6y']
        rows.append(row)
    return {'segments': rows, 'new_source_ranges': False, 'semantic_completion': False}


def build_report():
    text, basis = source_composed()
    doc = parse(text)
    if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
            (ROOT / 'data/kant-public-use-link-basis-v1.json').read_text(encoding='utf-8')) != basis:
        raise ValueError('Stored public-use linkage differs')
    for notation in ('compact', 'full'):
        form = format_graph(doc, notation)
        if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
            raise ValueError('Public-use link roundtrip differs')
    paths = [basis['document'], 'data/kant-public-use-link-basis-v1.json', PARENT, ROLES,
        'data/kant-open-access-basis-v1.json', 'data/kant-public-private-basis-v1.json', 'data/kant-public-private-alignment-v1.json',
        'scripts/compose_public_use_link.py', 'scripts/check_public_use_link.py', 'scripts/check_kant_roles.py', 'scripts/check_open_access.py',
        'noema/linking.py', 'noema/discourse.py', 'noema/finite_semantics.py', 'artifacts/written-units-v1/kant-1784.json']
    return {'status': 'linked_public_private_and_access_drafts_not_full_public_reason',
        'documents': {basis['document']: audit_basis(doc, basis)}, 'projections': projection_checks(),
        'replayed': replay_checks(), 'scope_equality_cases': scope_checks(), 'bridges': bridge_checks(), 'alignment': alignment(),
        'roundtrips': True, 'new_source_assertions': 0,
        'notation_size': {'canonical_source_document_characters': len(text),
            'added_characters': len(text) - len((ROOT / PARENT).read_text(encoding='utf-8'))},
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Public-use link report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Both original documents recovered; role, access and publication distinctions checked')


if __name__ == '__main__':
    main()
