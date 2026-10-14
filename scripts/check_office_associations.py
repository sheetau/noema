"""Check role-qualified membership and its use as the same undertaking scope."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_closed_policies import quoted
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts import check_solemn_undertakings as solemn
from scripts.compose_limits import call as k
from scripts.compose_office_associations import ROOT, PARENT, BUILDERS, POPULATION, OFFICE, ASSOCIATION, SOURCE, RELIGIOUS, UNDERTAKING, DESIGNATES
from scripts.compose_solemn_undertakings import SOURCE_PURPOSE

REPORT = ROOT / 'reports/office-associations-v1.json'
DOMAIN = ('alpha', 'beta', 'pact', 'other', 'rolea', 'roleb', 'churcha', 'churchb', 'acta', 'actb')
SCENES = solemn.mutual.SCENES
EXTRA = '''r jdagroup[] a.r jdaperson[] a.r jdaprin[] a.r jdarole[] a.r jdactx[] d.
r jdmembership[a a d] c.r jdhuman[a] c.r jdentrusted[a a d] c.
r jdserves[a a a d] c.r jddesignates[''' + DESIGNATES[2:-3] + '''] c.
r jdtasktruth[a d] c.
d jdtask[person a] e[b scene[k jdtasktruth[v person v scene]]].
d jdalias[person a] e[b scene[k jdtasktruth[v person v scene]]].
'''
REFS = dict(group='k jdagroup[]', person='k jdaperson[]', principal='k jdaprin[]', role='k jdarole[]',
    context='k jdactx[]', belongs='p jdmembership', human='p jdhuman', entrusted='p jdentrusted',
    serves='p jdserves', designates='p jddesignates', task='r[p jdtask]')


def setup(text, source=False):
    if source:
        refs = solemn.REFS | REFS | dict(context='k je[]')
        fields = (('hzcy', RELIGIOUS), ('hzcw', SOURCE_PURPOSE), ('hzcz', UNDERTAKING))
        extra = solemn.EXTRA + EXTRA
    else:
        refs = REFS; fields = (('rir', POPULATION), ('ris', OFFICE), ('rit', ASSOCIATION)); extra = EXTRA
    return candidate(text, extra + ''.join('q[' + k(name, *(refs[n] for n, _ in fields_)) + '].' for name, fields_ in fields))


def model_for(doc, bits=(True,) * 4, variant='baseline', source=False, base=None):
    model = dict(base) if base is not None else guarded(doc)
    human, commissioned, serving, designated = bits
    task = syntax(quoted('function_ref', 'jdalias' if variant == 'task_alias' else 'so' if source else 'jdtask'))
    members = () if variant == 'empty' else ('alpha',) if variant == 'one_member' else ('alpha', 'beta', 'pact') if variant in ('extra_qualified', 'extra_unqualified') else ('alpha', 'beta', 'other') if variant == 'self_member' else ('alpha', 'beta')
    roles = {'alpha': ('churcha', 'rolea'), 'beta': ('churchb', 'roleb')}
    if variant == 'same_principal': roles['beta'] = ('churcha', 'roleb')
    if variant == 'alternative_role': roles['alpha'] = ('churchb', 'roleb')
    if variant == 'extra_qualified': roles['pact'] = ('churcha', 'rolea')
    def belongs(group, person, scene):
        target = 'pact' if variant == 'other_group' else 'other'
        selected = ('alpha',) if variant == 'past_members' and scene in ('first', 'second') else members
        return group == target and person in selected and scene in ('first', 'second', 'now', 'future')
    def is_human(person): return person in ('alpha', 'beta', 'pact', 'other') and (person != 'alpha' or human)
    def entrusted(person, role, scene):
        if person not in roles: return False
        expected = 'roleb' if variant == 'split_role' and person == 'alpha' else roles[person][1]
        return (role, scene) == (expected, 'now') and (person != 'alpha' or commissioned) and not (variant == 'uncommissioned_beta' and person == 'beta')
    def serves(person, principal, role, scene):
        if person not in roles: return False
        organization = 'churchb' if variant == 'split_principal' and person == 'alpha' else roles[person][0]
        return (principal, role, scene) == (organization, roles[person][1], 'now') and (person != 'alpha' or serving)
    def designates(principal, role, description, scene):
        for person, (organization, office) in roles.items():
            time = 'future' if variant == 'split_time' and person == 'alpha' else 'now'
            if (principal, role, description.syntax, scene) == (organization, office, task, time) and (person != 'alpha' or designated): return True
        return False
    model.update(jdagroup=lambda: 'other', jdaperson=lambda: 'alpha', jdaprin=lambda: 'churcha', jdarole=lambda: 'rolea', jdactx=lambda: 'now',
        jdmembership=belongs, jdhuman=is_human, jdentrusted=entrusted, jdserves=serves, jddesignates=designates)
    if source:
        model.update(aa=is_human, cf=entrusted)
        if variant == 'outside_proponent': model['jwproponents'] = lambda person, scene: person == 'pact' and scene == 'now'
    return model


def evaluate(doc, model): return values(doc, model, DOMAIN, SCENES)


def generic_checks(texts):
    docs = [setup(t) for t in texts]; cases = []
    for bits in product((False, True), repeat=4):
        want = [bits[0], all(bits), all(bits)]
        rows = [evaluate(d, model_for(d, bits)) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Commission, service, designation or humanity omitted')
        cases.append(dict(bits=list(bits), results=want))
    contrasts = {}
    for variant in ('empty', 'one_member', 'other_group', 'self_member', 'extra_qualified', 'extra_unqualified', 'uncommissioned_beta',
        'same_principal', 'alternative_role', 'split_role', 'split_principal', 'split_time', 'task_alias', 'past_members'):
        if variant in ('empty', 'one_member', 'other_group', 'self_member'): want = [False, True, False]
        elif variant in ('extra_unqualified', 'uncommissioned_beta'): want = [True, True, False]
        elif variant == 'alternative_role': want = [True, False, True]
        elif variant in ('split_role', 'split_principal', 'split_time', 'task_alias'): want = [True, False, False]
        else: want = [True, True, True]
        rows = [evaluate(d, model_for(d, variant=variant)) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Association contrast ' + variant + ': ' + repr(rows))
        contrasts[variant] = want
    for d in docs:
        for name in ('jdmembership', 'jdhuman', 'jdentrusted', 'jdserves', 'jddesignates'):
            model = model_for(d); model[name] = guarded(d)[name]
            try: evaluate(d, model)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc): raise
            else: raise ValueError('Unknown membership or qualification guessed')
    return dict(cases=cases, contrasts=contrasts, standalone_agrees=True, task_not_executed=True, unknown_relations_refused=True)


def source_checks(texts):
    docs = [setup(t, True) for t in texts]
    bases = [solemn.model_for(d) for d in docs]
    cases = {}
    for variant in ('baseline', 'same_principal', 'past_members', 'extra_qualified', 'extra_unqualified', 'uncommissioned_beta',
        'one_member', 'other_group', 'split_role', 'split_principal', 'split_time', 'task_alias', 'outside_proponent'):
        if variant in ('baseline', 'same_principal', 'past_members'): want = [True, True, True]
        elif variant == 'extra_qualified': want = [True, True, False]
        elif variant == 'outside_proponent': want = [True, False, False]
        else: want = [False, True, False]
        rows = [evaluate(d, model_for(d, variant=variant, source=True, base=b)) for d, b in zip(docs, bases)]
        if rows != [want] * len(docs): raise ValueError('Association/undertaking scope contrast ' + variant + ': ' + repr(rows))
        cases[variant] = want
    for d, b in zip(docs, bases):
        # so, doctrine truth, performance, belief and permission are not evaluated.
        if evaluate(d, model_for(d, source=True, base=b)) != [True] * 3: raise ValueError('Qualification executed the task')
        for notation in ('compact', 'full'):
            form = format_graph(d, notation)
            if parse(form) != d or parse(decode(encode(form, 'v2'))) != d: raise ValueError('Office association query roundtrip differs')
    return dict(cases=cases, standalone_agrees=True, parties_share_membership=True, membership_fixed_at_anchor=True,
        distinct_principals_allowed=True, actual_tasks_not_required=True, closed_roundtrips=True)


def cross_domain_checks(text):
    doc = setup(text, True); doc['statements'] = doc['statements'][:1]
    refs = REFS | dict(task='r[p sq]', context='k je[]')
    doc = parse(format_graph(doc, 'compact') + 'q[' + k('hzcx', *(refs[n] for n, _ in SOURCE)) + '].')
    base = solemn.model_for(doc); cases = {}
    for task, want in (('so', [True, False]), ('sq', [False, True])):
        model = model_for(doc, source=True, base=base)
        expected = syntax(quoted('function_ref', task))
        model['jddesignates'] = lambda principal, role, content, scene: (principal, role) in (('churcha', 'rolea'), ('churchb', 'roleb')) and content.syntax == expected and scene == 'now'
        result = evaluate(doc, model)
        if result != want: raise ValueError('Task description changed the institution schema or erased its domain')
        cases[task] = result
    return dict(cases=cases, new_noun_primitives=0, health_and_religious_judgment_descriptions=True,
        whole_clergy_or_medical_profession_not_claimed=True)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Stored office association differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Office association roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
        sizes[stem] = dict(characters=len(text), statements=len(doc['statements']))
    doc, parent = parse(texts[1]), parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']: raise ValueError('Parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0013')
    phrase = 'Gesellschaft von Geistlichen'
    if unit['text'].count(phrase) != 1: raise ValueError('Ambiguous source phrase')
    start = unit['text'].index(phrase)
    segment = dict(unit=unit['id'], unit_sha256=unit['text_sha256'], status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase, definitions=['rit', 'hzcx', 'hzcy', 'hzcz'])
    paths = [*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_office_associations.py', 'scripts/check_office_associations.py', 'scripts/check_solemn_undertakings.py',
        'scripts/check_mutual_undertakings.py', 'scripts/check_purposive_undertakings.py', 'scripts/check_closed_policies.py',
        'scripts/check_conditional_release.py', 'scripts/check_described_appraisals.py', 'scripts/check_public_assessment.py', 'scripts/check_rod_setup.py',
        'noema/finite_semantics.py', 'noema/extraction.py', 'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_office_association_interpretation', documents=documents, sizes=sizes,
        generic=generic_checks([texts[0], texts[2]]), source=source_checks(texts[1:]), cross_domain=cross_domain_checks(texts[1]),
        alignment=dict(segments=[segment], semantic_completion=False), new_definitions=7, new_primitives=0, new_author_statements=0,
        parent_preserved=True, roundtrips=True, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in paths})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); options = parser.parse_args()
    report = build_report()
    if options.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Office association report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream: json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Commissioned task roles, distinct institutions and shared membership/undertaking scope checked')


if __name__ == '__main__': main()
