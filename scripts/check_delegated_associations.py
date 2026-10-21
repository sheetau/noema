"""Check complete constituencies, same mandates, mixed offices and fixed parties."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, validate_hashes
from noema.script import transcribe
from scripts.compose_delegated_associations import ROOT, LIBRARY, BASIS, MEANINGS, PRIMITIVES, parent, build, closure
from scripts.fetch_delegated_associations_evidence import EVIDENCE, validate as validate_evidence
from scripts.check_motive_causes import unknown, symbol
from scripts.check_pastoral_roles import evaluate

REPORT = 'reports/delegated-associations-v1.json'
DOC = 'docs/delegated-associations-v1.md'
PRIORS = ('reports/fifth-paragraph-v1.json', 'reports/clerical-audiences-v1.json', 'reports/confessional-teaching-v1.json')
DOMAIN = ('assembly', 'alice', 'bert', 'elder', 'rolea', 'roleb', 'churcha', 'churchb', 'other')
SCENES = ('reference', 'past', 'future')
EXTRA = ''.join('r z' + n + '[] a.' for n in DOMAIN) + 'r zref[] d.r zpast[] d.r zfuture[] d.'
EXTRA += ('r zmember[a a d] c.r zrepresented[a a d] c.r zmandate[a a a a d] c.'
          'r zhuman[a] c.r zqual[a d] c.r zoffice[a a a d] c.r zinstitution[a d] c.')
GENERIC = 'k zassembly[] k zref[] p zmember p zrepresented p zmandate p zhuman p zinstitution p zoffice'


def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(roots, query, boundaries=(), extra=EXTRA):
    doc = deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']]); d.pop('body')
    doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + extra + query)


def base(doc):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    v.update({'z' + n: lambda n=n: n for n in DOMAIN})
    v.update(zref=lambda: 'reference', zpast=lambda: 'past', zfuture=lambda: 'future')
    return v


def run(doc, values): return evaluate(doc, values, DOMAIN, SCENES, True)


def model(doc, variant='baseline'):
    v = base(doc)
    members = {'alice', 'bert'}
    represented = {'churcha', 'churchb'}
    offices = {('alice', 'rolea', 'churcha'), ('bert', 'roleb', 'churchb'), ('elder', 'roleb', 'churchb')}
    mandates = {('churcha', 'alice', 'rolea', 'assembly', 'reference'),
                ('churchb', 'bert', 'roleb', 'assembly', 'reference')}
    if variant == 'empty': members.clear()
    if variant == 'singleton': members.remove('bert')
    if variant == 'self_member': members.add('assembly')
    if variant in ('extra_member', 'mixed_offices'): members.add('elder')
    if variant == 'mixed_offices': mandates.add(('churchb', 'elder', 'roleb', 'assembly', 'reference'))
    if variant == 'no_constituents': represented.clear()
    if variant == 'extra_constituent': represented.add('other')
    if variant == 'hidden_constituent': represented.remove('churchb')
    if variant == 'missing_delegate': mandates = {m for m in mandates if m[1] != 'bert'}
    if variant == 'unqualified_delegate': offices.remove(('bert', 'roleb', 'churchb'))
    if variant.startswith('mandate_'):
        index = dict(principal=0, person=1, role=2, assembly=3, reference=4)[variant[8:]]
        row = ['churchb', 'bert', 'roleb', 'assembly', 'reference']; row[index] = 'past' if index == 4 else 'other'
        mandates = {m for m in mandates if m[1] != 'bert'} | {tuple(row)}
    if variant == 'split_principal': offices.remove(('bert', 'roleb', 'churchb')); offices.add(('bert', 'roleb', 'churcha'))
    if variant == 'split_role': offices.remove(('bert', 'roleb', 'churchb')); offices.add(('bert', 'rolea', 'churchb'))
    if variant == 'alternative_role':
        offices.add(('bert', 'rolea', 'churchb')); mandates.add(('churchb', 'bert', 'rolea', 'assembly', 'reference'))
    if variant == 'one_rep_two_principals':
        offices.add(('alice', 'rolea', 'churchb')); mandates.add(('churchb', 'alice', 'rolea', 'assembly', 'reference'))
    humans = {'alice', 'bert', 'elder'}
    if variant == 'nonhuman': humans.remove('bert')
    def member(group, person, ref):
        if variant == 'wrong_membership_reference': ref = 'wrong'
        if variant == 'wrong_group': group = 'other'
        if group != 'assembly': return False
        return person in (members if ref == 'reference' else {'elder'} if ref == 'past' else {'alice'} if ref == 'future' else set())
    def constituent(group, principal, ref):
        return (group, ref) == ('assembly', 'reference') and principal in represented
    def mandate(principal, person, role, group, ref): return (principal, person, role, group, ref) in mandates
    def office(person, role, principal, ref): return ref == 'reference' and (person, role, principal) in offices
    v.update(zmember=member, zrepresented=constituent, zmandate=mandate, zhuman=lambda p: p in humans,
        zqual=lambda p, r: r == 'reference' and p in ('alice', 'bert'), zoffice=office,
        zinstitution=lambda p, r: r == 'reference' and p in ('churcha', 'churchb') and not (variant == 'not_institution' and p == 'churchb'),
        h246c=member, h254g=constituent, h254f=mandate, aa=lambda p: p in humans,
        hzwn=lambda p, role, ref: ref == 'reference' and any((p, role) == row[:2] for row in offices),
        hzxf=office, h246k=lambda p, principal, role, ref: office(p, role, principal, ref),
        si=lambda p, code, ref: p in ('alice', 'bert') and (symbol(code), code.rank, ref) == ('so', 0, 'reference'),
        hzwo=lambda role, code, ref: role in ('rolea', 'roleb') and (symbol(code), code.rank, ref) == ('so', 0, 'reference'),
        hzwu=lambda role, code, ref: role in ('rolea', 'roleb') and (symbol(code), code.rank, ref) == ('so', 0, 'reference'),
        hzxg=lambda role, code, church, ref: (role, church) in {row[1:] for row in offices} and (symbol(code), code.rank, ref) == ('hzxi', 0, 'reference'))
    if 'r35r' in v:
        v['r35r'] = lambda church, creed, subject, ref: v['zinstitution'](church, ref) and (creed, subject) == ('other', 'other')
    return v


@lru_cache(None)
def population_checks():
    doc = fixture(('r454',), 'q[k r454[k zassembly[] k zref[] p zmember p zhuman p zqual]].')
    rows = {}
    for variant in ('baseline', 'empty', 'singleton', 'self_member', 'extra_member', 'nonhuman', 'wrong_group', 'wrong_membership_reference'):
        result = run(doc, model(doc, variant)); assert result == [variant == 'baseline'], (variant, result); rows[variant] = result[0]
    # The same association pattern classifies a different task, with no change
    # to the language definition and no assumption that all work is clerical.
    v = model(doc); v['zqual'] = lambda p, r: r == 'reference' and p in ('alice', 'bert', 'elder')
    assert run(doc, v) == [True]
    return dict(complete_membership_contrasts=rows,qualification_is_parameter_not_membership_filter=True)


@lru_cache(None)
def delegation_checks():
    doc = fixture(('r457',), 'q[k r457[' + GENERIC + ']].')
    variants = ('baseline', 'mixed_offices', 'alternative_role', 'one_rep_two_principals', 'empty', 'singleton',
        'self_member', 'extra_member', 'no_constituents', 'extra_constituent', 'hidden_constituent', 'missing_delegate',
        'unqualified_delegate', 'split_principal', 'split_role', 'nonhuman', 'not_institution', 'wrong_group', 'wrong_membership_reference',
        *('mandate_' + n for n in ('principal', 'person', 'role', 'assembly', 'reference')))
    rows = {}
    for variant in variants:
        result = run(doc, model(doc, variant))
        assert result == [variant in ('baseline', 'mixed_offices', 'alternative_role', 'one_rep_two_principals')], (variant, result)
        rows[variant] = result[0]
    return dict(native_complete_members_and_constituents=rows,nonunique_representation_allowed=True)


@lru_cache(None)
def role_checks():
    doc = fixture(('r455', 'r46b'), 'q[k r455[k zalice[] k zrolea[] k zchurcha[] k zref[]]].q[k r46b[k zalice[] k zrolea[] k zchurcha[] k zref[]]].')
    rows = []
    for bits in product((False, True), repeat=4):
        v = model(doc)
        for bit, name in zip(bits, ('aa', 'hzwn', 'hzxf', 'h246k')):
            old = v[name]; v[name] = lambda *args, bit=bit, old=old: bit and old(*args)
        result = run(doc, v); assert result == [all(bits), all(bits)], (bits, result); rows.append([*bits, *result])
    for name in ('hzwn', 'hzxf', 'h246k'):
        v = model(doc); v[name] = lambda *args: 'other' in args
        assert run(doc, v) == [False, False]
    # r455 executes existing r35m, with its actual role/appointment/duty code.
    # Neither role classification executes the quoted religious practice.
    v = model(doc); assert v['dg'] is unknown and run(doc, v) == [True, True]
    return dict(native_clerical_and_institutional_role_matrix=rows,same_person_role_principal=True,religious_practice_not_executed=True)


@lru_cache(None)
def source_checks():
    doc = fixture(('r456', 'r46c'), 'q[k r456[k zassembly[] k zref[]]].q[k r46c[k zassembly[] k zref[]]].', ('r35r',))
    rows = {}
    for variant, expected in (
        ('baseline', [True, True]), ('mixed_offices', [False, True]), ('extra_member', [False, False]),
        ('missing_delegate', [True, False]), ('not_institution', [True, False]), ('hidden_constituent', [True, False]),
        ('extra_constituent', [True, False]), ('mandate_role', [True, False]), ('unqualified_delegate', [False, False])):
        result = run(doc, model(doc, variant)); assert result == expected, (variant, result); rows[variant] = result
    quoted = fixture(('r46c',), 'r zshown[i[h[a d] c]] c.q[k zshown[r[p r46c]]].', extra='')
    v = base(quoted); v['zshown'] = lambda code: code.rank == 0 and symbol(code) == 'r46c'
    assert run(quoted, v) == [True]
    return dict(clerical_then_delegated_contrasts=rows,source_boundary='r35r only; unchanged church definition pinned by confessional-teaching report',
        native_member_clerical_and_institutional_roles=True,assembly_can_be_quoted_without_asserting_existence=True)


@lru_cache(None)
def parties_checks():
    query = ''.join('q[c[k r46a[k zassembly[] k zref[] p h246c]][k z' + p + '[] k z' + t + '[]]].'
                    for p in ('alice', 'bert', 'elder') for t in ('ref', 'past', 'future'))
    doc = fixture(('r46a', 'h246c'), query)
    rows = {}
    for variant, wanted in (('baseline', [True]*6 + [False]*3), ('extra_member', [True]*9)):
        result = run(doc, model(doc, variant)); assert result == wanted, (variant, result); rows[variant] = result
    return dict(fixed_membership_at_three_evaluation_points=rows,unqualified_member_is_not_dropped_from_parties=True,
        no_oath_or_legal_permission_asserted=True)


@lru_cache(None)
def unknown_checks():
    doc = fixture(('r46c',), 'q[k r46c[k zassembly[] k zref[]]].', ('r35r',))
    rows = []
    for name in ('h246c', 'h254g', 'h254f', 'hzwn', 'hzxf', 'h246k', 'r35r'):
        v = model(doc); v[name] = unknown
        try: run(doc, v)
        except ValueError as error: assert 'Unknown' in str(error), str(error); rows.append(name)
        else: raise AssertionError(name)
    return dict(unknown_not_false=rows)


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    for n, e in new.entries.items():
        if n not in MEANINGS and n not in PRIMITIVES:
            assert e['declaration'] == old.entries[n]['declaration'] and e['meaning_ja'] == old.entries[n]['meaning_ja'], n
    for path, body in build().items(): assert (ROOT / path).read_text(encoding='utf-8') == body, path
    for notation in ('compact', 'full'):
        body = format_graph(new.document, notation)
        assert parse(body) == parse(transcribe(body, alphabet='v2')) == new.document
    for path in PRIORS: validate_hashes(ROOT, read(path)['source_sha256'])
    validate_evidence(read(EVIDENCE))
    assert not new.document['statements'] and len(old.document['statements']) == 96
    assert new.entries['h254f']['arguments'] == ['principal', 'person', 'role', 'assembly', 'reference']
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        historical_evidence_pinned=True,no_new_source_sentence=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items(): write_exact(ROOT / path, body)


def build_report():
    results = {}
    for name, fn in [('population', population_checks), ('delegation', delegation_checks), ('roles', role_checks),
                     ('source', source_checks), ('parties', parties_checks), ('unknown', unknown_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    evidence = read(EVIDENCE)
    paths = set(build()) | set(catalog().source_sha256) | set(PRIORS) | {DOC, EVIDENCE,
        evidence['source']['inventory'], evidence['primary_page']['path'], *[s['path'] for s in evidence['sources']],
        'scripts/compose_delegated_associations.py', 'scripts/check_delegated_associations.py',
        'scripts/fetch_delegated_associations_evidence.py', 'tests/test_delegated_associations.py',
        'scripts/check_motive_causes.py', 'scripts/check_pastoral_roles.py', 'scripts/compose_grounded_step.py',
        'scripts/compose_qualitative_influence.py', 'scripts/compose_spiritual_guardians.py'}
    return dict(status='distinct_clerical_and_delegated_memberships', document=LIBRARY, **results,
        whole_sentence_semantically_verified=False, verified_full_units={'kant-1784':0, 'einstein-1905':0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
