"""Check a substantive permission criterion through closed policy composition."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from itertools import product
from noema.constructed import parse, format_graph
from noema.script import transcribe
from scripts.compose_public_reason_claim import ROOT, PARENT, SOURCE, CORE, EXAMPLE, BASIS, build, basis
from scripts.check_caused_choice import evaluate
from scripts.check_scoped_counts import arithmetic
from scripts.check_thinking_disposition import code_is, forbidden
from scripts.check_apparent_liberty import UNITS
from scripts import check_political_consequence as political

REPORT = ROOT / 'reports/public-reason-claim-v1.json'
DOMAIN = ('norm', 'government', 'office', 'person', 'other', 'first', 'second', 'duty', 'scholar', 'secondrole', 'audience')
SCENES = ('now', 'low', 'high')


@lru_cache(maxsize=4)
def document(path): return parse((ROOT / path).read_text(encoding='utf-8'))


def permission_model(*, allowed=3, prohibited=0, variant='baseline', calls=None):
    def classification(person, activity, point):
        return variant != 'empty_public' and person == 'person' and activity in ('first', 'second', 'duty')
    def role(person, activity, role, point):
        expected = 'office' if activity == 'duty' else 'secondrole' if activity == 'second' else 'scholar'
        return person == 'person' and role == expected
    def norm(source, person, role, activity, desc, polarity, point, *, permission):
        if calls is not None: calls.append(('permission' if permission else 'prohibition', source, person, role, activity, desc, polarity, point))
        if variant == 'unknown_permission' and permission: raise ValueError('Unassessed public permission')
        expected = dict(source='government', person='person', role='secondrole' if activity == 'second' else 'scholar',
            activity=activity, description='zzq', context=point, polarity=permission)
        if permission and variant in ('source', 'person', 'role', 'activity', 'description', 'context', 'polarity'):
            expected[variant] = not permission if variant == 'polarity' else 'other'
        match = (source, person, role, activity, point, polarity) == tuple(expected[key] for key in ('source','person','role','activity','context','polarity'))
        if not match or not code_is(desc, expected['description']): return False
        bit = 1 if activity == 'first' else 2 if activity == 'second' else 0
        if variant == 'missing_current' and point == 'now' and permission: return False
        return bool((allowed if permission else prohibited) & bit)
    return dict(aa=lambda person: person == 'person' and variant != 'nonhuman', ca=classification, cb=role,
        cc=lambda activity, audience, point: activity in ('first', 'second') and audience == 'audience',
        cd=lambda role, point: role in ('scholar', 'secondrole'), ce=lambda audience, point: audience == 'audience',
        cg=forbidden, h7a=lambda *args: norm(*args, permission=False), h7b=lambda *args: norm(*args, permission=True))


def values(allowed=3, prohibited=0, norms=7, *, variant='baseline', memoize=True, calls=None):
    def required(source, actor, office, target, bindings, polarity, point):
        if calls is not None: calls.append(('requirement', source, actor, office, target, bindings.items, polarity, point))
        if variant == 'unknown_requirement': raise ValueError('Unassessed criterion requirement')
        expected = ('government', 'other') if variant == 'norm_person' else ('government', 'person')
        name = 'jwpolicy' if variant == 'norm_description' else 'iavclaim'
        return (source, actor, office) == ('norm', 'government', 'office') and bindings.items == expected and polarity and code_is(target, name) and bool(norms & (1 << SCENES.index(point)))
    p = dict(arithmetic(), **permission_model(allowed=allowed, prohibited=prohibited, variant=variant, calls=calls),
        jwsource=lambda: 'norm', jwactor=lambda: 'government', jwoffice=lambda: 'office', jwperson=lambda: 'person',
        jwnow=lambda: 'now', jwscope=lambda person: person == 'person' and variant != 'wrong_scope',
        jwcases=lambda point: point in ('low', 'high') and variant != 'empty_cases', h7k=required)
    doc = document(EXAMPLE)
    p = {d['name']: p.get(d['name'], forbidden) for d in doc['declarations'] if d['kind'] == 'primitive'}
    return evaluate(doc, p, DOMAIN, SCENES, memoize=memoize)


@lru_cache(maxsize=1)
def source_fixture():
    doc = deepcopy(political.source_fixture())
    names = {d['name'] for d in doc['declarations']}
    for d in document(EXAMPLE)['declarations']:
        if d['name'] not in names: doc['declarations'].append(deepcopy(d)); names.add(d['name'])
    new = next(d for d in doc['declarations'] if d['name'] == 'jpnew')
    new['body'] = deepcopy(next(d for d in doc['declarations'] if d['name'] == 'jwpolicy')['body'])
    doc['declarations'].remove(new); doc['declarations'].append(new)
    return parse(format_graph(doc, 'compact'))


def source_values(*, variant='baseline', indices=(2,)):
    p, domain, scenes = political.source_model()
    original = p['h7k']
    def required(source, actor, office, target, bindings, polarity, point):
        if code_is(target, 'iavclaim'):
            return variant != 'missing_requirement' and (source, actor, office) == ('norm','government','office') and bindings.items == ('government','person') and polarity
        return original(source, actor, office, target, bindings, polarity, point)
    permissions = permission_model(allowed=1 if variant == 'missing_permission' else 3)
    # Keep the original model's other human cohort members. The new policy
    # selects one beneficiary, not the entire human domain.
    permissions.pop('aa')
    p.update(permissions)
    p.update(jwsource=lambda: 'norm', jwactor=lambda: 'government', jwoffice=lambda: 'office', jwperson=lambda: 'person',
        jwnow=lambda: 'normbase', jwscope=lambda person: person == 'person', jwcases=lambda point: point in ('normbase','normchanged'), h7k=required)
    doc = deepcopy(source_fixture()); doc['statements'] = [doc['statements'][i] for i in indices]
    p = {d['name']: p.get(d['name'], forbidden) for d in doc['declarations'] if d['kind'] == 'primitive'}
    return evaluate(doc, p, domain + tuple(x for x in DOMAIN if x not in domain), scenes, budget=60_000_000)


def alignment():
    unit = next(u for u in json.loads((ROOT / UNITS).read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0017')
    return dict(unit=unit['id'], text_sha256=unit['text_sha256'], status='explicit_interpretive_annotation',
        definitions=['iavclaim', 'iavpolicy', 'iavtreatment'], adds_new_text_coverage=False, semantic_completion=False,
        concrete_permission_criterion=True, dignity_content_incomplete=True)


def build_report():
    documents = {}
    for path, text in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == text
        doc = parse(text)
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            assert parse(form) == doc and parse(transcribe(form, alphabet='v2')) == doc
        documents[path] = dict(declarations=len(doc['declarations']), statements=len(doc['statements']), characters=len(text))
    assert json.loads((ROOT / BASIS).read_text(encoding='utf-8')) == basis()
    for allowed, prohibited in product(range(4), repeat=2):
        good = allowed == 3 and prohibited == 0
        assert values(allowed, prohibited) == [good, good, good, True]
    for norms in range(8): assert values(norms=norms) == [True, norms == 7, norms == 7, True]
    assert values(memoize=False) == values()
    assert source_values() == [True]
    old, new = document(PARENT), document(SOURCE)
    assert new['declarations'][:len(old['declarations'])] == old['declarations'] and new['statements'] == old['statements']
    paths = [PARENT, SOURCE, CORE, EXAMPLE, BASIS, UNITS, 'scripts/compose_public_reason_claim.py',
        'scripts/check_public_reason_claim.py', 'tests/test_public_reason_claim.py', 'docs/public-reason-claim-v1.md',
        'scripts/check_political_consequence.py', 'scripts/check_caused_choice.py', 'noema/constructed_specialization.py',
        'noema/constructed.py', 'noema/constructed_discourse.py', 'noema/constructed_semantics.py',
        'noema/constructed_closure_semantics.py', 'noema/diagnostic_short_circuit.py']
    return dict(status='public_permission_claim_compiled_and_connected', documents=documents, permission_profiles=16,
        requirement_profiles=8, source_alignment=alignment(), roundtrips=True, limitations=basis()['limitations'],
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths})


def main():
    cli = argparse.ArgumentParser(description=__doc__); cli.add_argument('--verify-only', action='store_true'); args = cli.parse_args()
    report = build_report()
    if args.verify_only: assert json.loads(REPORT.read_text(encoding='utf-8')) == report
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream: json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Concrete public permission criterion verified; dignity and full-source equivalence remain incomplete')


if __name__ == '__main__': main()
