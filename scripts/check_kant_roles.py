"""Countermodels for normative sources, roles and the public/private distinction."""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path

from noema.finite_semantics import Content, evaluate_document
from noema.grammar import parse, format_graph, number_word
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.compose_kant_roles import compose, composed_basis

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/kant-public-private-v1.json'


def query(doc, symbol, args, primitives, individuals, situations, at=None):
    doc, primitives = deepcopy(doc), dict(primitives)
    arguments = []
    for i, (sort, value) in enumerate(args):
        name = 'z' + number_word(i)
        doc['declarations'].append({'kind': 'primitive', 'name': name, 'parameters': [], 'result': sort})
        primitives[name] = lambda value=value: value
        arguments.append({'kind': 'call', 'symbol': name, 'arguments': []})
    body = {'kind': 'call', 'symbol': symbol, 'arguments': arguments}
    if at is not None:
        doc['declarations'].append({'kind': 'primitive', 'name': 'zz', 'parameters': [], 'result': 'situation'})
        primitives['zz'] = lambda: at
        body = {'kind': 'evaluate', 'content': body, 'situation': {'kind': 'call', 'symbol': 'zz', 'arguments': []}}
    doc['statements'] = [{'kind': 'ask', 'body': body}]
    return evaluate_document(doc, individuals=individuals, situations=situations, primitives=primitives, max_steps=2000000)[0]['value']


def normative_checks():
    doc = parse((ROOT / 'examples/v011/normative-roles.noema').read_text(encoding='utf-8'))
    individuals = ('source', 'other_source', 'person', 'other_person', 'role', 'other_role')
    situations = ('now', 'fulfilled', 'elsewhere')
    goal = Content(situations, (False, True, False))
    opposite = tuple(not x for x in goal.values)
    results = {}
    def check(label, symbol, expected, *, required=(), allowed=(), source='source', person='person', role='role', now='now', content=goal):
        def obligation(s, p, r, g, w):
            return (s, p, r) == ('source', 'person', 'role') and g.values in required
        def authorization(s, p, r, g, w):
            return (s, p, r) == ('source', 'person', 'role') and g.values in allowed
        args = [('individual', v) for v in (source, person, role)] + [('content', content), ('situation', now)]
        actual = query(doc, symbol, args, {'aa': obligation, 'ab': authorization}, individuals, situations)
        if actual != expected:
            raise ValueError('Normative countermodel failed: ' + label)
        results[label] = {'expected': expected, 'actual': actual}
    check('required_but_unfulfilled', 'bc', True, required=(goal.values,))
    check('required_and_fulfilled', 'bc', False, required=(goal.values,), now='fulfilled')
    check('other_role_not_bound', 'bc', False, required=(goal.values,), role='other_role')
    check('other_person_not_bound', 'bc', False, required=(goal.values,), person='other_person')
    check('other_source_not_merged', 'bc', False, required=(goal.values,), source='other_source')
    check('no_prohibition', 'bg', True)
    check('no_prohibition_is_not_authorization', 'bf', False)
    check('authorized_without_actual_performance', 'bf', True, allowed=(goal.values,))
    check('opposing_requirements_are_detected', 'bd', True, required=(goal.values, opposite))
    check('opposing_requirements_do_not_impose_unrelated_content', 'aa', False,
          required=(goal.values, opposite), content=Content(situations, (True, True, False)))
    check('authorization_and_prohibition_conflict', 'be', True, required=(opposite,), allowed=(goal.values,))
    check('conflicting_authorization_is_not_uncontested', 'bf', False, required=(opposite,), allowed=(goal.values,))
    return results


def role_checks():
    doc = parse(compose())
    individuals = ('person', 'other', 'scholar', 'officer', 'office', 'author', 'regime', 'regulator',
                   'essay', 'duty', 'readers', 'congregation')
    situations = ('now', 'essay_done', 'duty_done', 'public_free', 'private_restricted', 'both')
    essay = tuple(s == 'essay_done' for s in situations)
    duty = tuple(s == 'duty_done' for s in situations)
    rights = tuple(s in ('public_free', 'both') for s in situations)
    restriction = tuple(s in ('private_restricted', 'both') for s in situations)

    def model(*, audience='readers', scholar_role=True, performs=True, everywhere=True, entrusted=True, public_forbidden=False):
        def required(source, person, role, content, scene):
            if (source, person, role) == ('author', 'regulator', 'office'):
                return content.values == rights and (everywhere or scene == 'now')
            if public_forbidden and (source, person, role) == ('regime', 'person', 'scholar'):
                return content.values == tuple(not x for x in essay)
            return ((source, person, role) == ('regime', 'person', 'officer')
                    and content.values == tuple(not x for x in duty) and scene in ('private_restricted', 'both'))
        def authorized(source, person, role, content, scene):
            if (source, person, role) == ('author', 'regulator', 'office'):
                return content.values == restriction
            return ((source, person, role) == ('regime', 'person', 'scholar')
                    and content.values == essay and scene in ('public_free', 'both'))
        return {
            'aa': required, 'ab': authorized,
            'ca': lambda person, activity, scene: person == 'person' and activity in ('essay', 'duty'),
            'cb': lambda person, activity, role, scene: (person, activity, role) in (('person', 'essay', 'scholar'), ('person', 'duty', 'officer')),
            'cc': lambda activity, readers, scene: (activity, readers) in (('essay', audience), ('duty', 'congregation')),
            'cd': lambda role, scene: scholar_role and role == 'scholar',
            'ce': lambda readers, scene: readers == 'readers',
            'cf': lambda person, role, scene: entrusted and (person, role) == ('person', 'officer'),
            'cg': lambda person, activity, scene: performs and person == 'person' and (
                (activity, scene) in (('essay', 'essay_done'), ('duty', 'duty_done')))}
    results = {}
    def check(label, symbol, values, expected, *, at=None, **changes):
        args = [('situation' if value in situations else 'individual', value) for value in values]
        actual = query(doc, symbol, args, model(**changes), individuals, situations, at)
        if actual != expected:
            raise ValueError('Role countermodel failed: ' + label)
        results[label] = {'expected': expected, 'actual': actual}
    check('scholar_to_reader_world', 'da', ('person', 'essay', 'scholar', 'now'), True)
    check('public_classification_does_not_require_execution', 'da', ('person', 'essay', 'scholar', 'now'), True, performs=False)
    check('same_person_in_civic_office', 'db', ('person', 'duty', 'officer', 'now'), True)
    check('office_status_does_not_make_all_acts_private', 'db', ('person', 'essay', 'scholar', 'now'), False)
    check('job_speech_to_congregation_is_not_public_use', 'da', ('person', 'duty', 'officer', 'now'), False)
    check('readership_alone_is_not_scholarly_capacity', 'da', ('person', 'essay', 'scholar', 'now'), False, scholar_role=False)
    check('congregation_is_not_reader_world', 'da', ('person', 'essay', 'scholar', 'now'), False, audience='congregation')
    check('unentrusted_role_is_not_private_by_default', 'db', ('person', 'duty', 'officer', 'now'), False, entrusted=False)
    rights_args = ('regime', 'person', 'scholar')
    check('public_permission_not_actual_now', 'dd', rights_args, False, at='now')
    check('public_permission_in_other_case', 'dd', rights_args, True, at='public_free')
    check('conflicting_prohibition_prevents_uncontested_public_permission', 'dd', rights_args, False, at='public_free', public_forbidden=True)
    meta = ('author', 'regulator', 'office', 'regime', 'person')
    check('ought_to_authorize_despite_current_restriction', 'df', (*meta, 'scholar', 'now'), True)
    check('may_restrict_private_use', 'dg', (*meta, 'officer', 'now'), True)
    check('permission_to_restrict_is_not_actual_restriction', 'de', ('regime', 'person', 'officer'), False, at='now')
    check('private_restriction_in_other_case', 'de', ('regime', 'person', 'officer'), True, at='private_restricted')
    check('always_requires_all_contexts', 'dh', (*meta, 'scholar'), True)
    check('one_context_does_not_establish_always', 'dh', (*meta, 'scholar'), False, everywhere=False)
    return results


def build_report():
    normative, roles = normative_checks(), role_checks()
    text, basis = compose(), composed_basis()
    if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
        raise ValueError('Stored role draft differs')
    if json.loads((ROOT / 'data/kant-public-private-basis-v1.json').read_text(encoding='utf-8')) != basis:
        raise ValueError('Stored role basis differs')
    doc = parse(text)
    alignment = json.loads((ROOT / 'data/kant-public-private-alignment-v1.json').read_text(encoding='utf-8'))
    inventory = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    source_path = ROOT / 'artifacts/written-units-v1/kant-1784.json'
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != inventory['works']['kant-1784']['units_sha256']:
        raise ValueError('Source unit artifact changed')
    unit = next(u for u in json.loads(source_path.read_text(encoding='utf-8'))['units'] if u['id'] == alignment['source_unit'])
    if (alignment['document'] != basis['document'] or unit['text_sha256'] != alignment['source_sha256']
            or alignment['unselected_ranges_status'] != 'pending'):
        raise ValueError('Alignment source or document differs')
    ranges, end = [], 0
    for selection in alignment['selections']:
        if not selection['source'] or unit['text'].count(selection['source']) != 1:
            raise ValueError('Source excerpt missing or ambiguous')
        start = unit['text'].index(selection['source'])
        if start < end or selection['status'] != 'partial' or not set(selection['definitions']) <= set(basis['definitions']):
            raise ValueError('Invalid selection range or status')
        if start > end:
            ranges.append({'start': end, 'end': start, 'status': 'pending'})
        end = start + len(selection['source'])
        ranges.append({'id': selection['id'], 'start': start, 'end': end, 'status': 'partial',
                       'definitions': selection['definitions']})
    if end < len(unit['text']):
        ranges.append({'start': end, 'end': len(unit['text']), 'status': 'pending'})
    for notation in ('compact', 'full'):
        canonical = format_graph(doc, notation)
        if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
            raise ValueError('Role draft round trip differs')
    paths = ['examples/v011/normative-roles.noema', 'examples/fragments/kant-public-private.noema.inc',
             'examples/v011/kant-public-private.noema', 'data/normative-roles-basis-v1.json',
             'data/kant-roles-additions-v1.json', 'data/kant-public-private-basis-v1.json',
             'data/kant-public-private-alignment-v1.json', 'reports/written-units-v1.json',
             'scripts/compose_kant_roles.py', 'scripts/check_kant_roles.py', 'noema/discourse.py', 'noema/finite_semantics.py']
    return {'status': 'partial_semantic_draft', 'normative_countermodels': normative, 'role_countermodels': roles,
            'basis_audit': audit_basis(doc, basis), 'roundtrip': True, 'source_unit': unit['id'],
            'source_ranges': ranges, 'unselected_source_ranges_accounted_for': True, 'verified_full_units': 0,
            'source_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Role verification differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Kant roles: normative and role countermodels reproduced; full source coverage remains incomplete')


if __name__ == '__main__':
    main()
