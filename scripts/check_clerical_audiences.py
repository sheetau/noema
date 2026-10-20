"""Check institutional role witnesses and both complete recipient ranges."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, validate_hashes
from noema.script import transcribe
from scripts.compose_clerical_audiences import ROOT, LIBRARY, BASIS, PRIMITIVES, MEANINGS, parent, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

REPORT = 'reports/clerical-audiences-v1.json'
DOC = 'docs/clerical-audiences-v1.md'
PRIOR = 'reports/public-civic-opinion-v1.json'
EVIDENCE = 'data/clerical-teaching-lexical-v1.json'
DOMAIN = ('person', 'role', 'church', 'congregation', 'students', 'members', 'course', 'subject', 'learner', 'member', 'overlap', 'other')
SCENES = ('reference', 'other')
EXTRA = ''.join('r z' + n + '[] a.' for n in DOMAIN) + 'r zref[] d.'


def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(target):
    doc = deepcopy(catalog().document); doc.update(declarations=closure(doc, [target]), statements=[])
    names = dict(r35m=('person', 'role', 'church'), r35n=('course', 'subject'),
        r35o=('person', 'role', 'church', 'learner'), r35p=('congregation', 'member'),
        r35q=('person', 'role', 'church', 'congregation', 'students', 'members'))[target]
    call = 'k ' + target + '[' + ' '.join('k z' + n + '[]' for n in names) + ' k zref[]]'
    return parse(format_graph(doc, 'compact') + EXTRA + 'q[' + call + '].')


def model(doc, variant='baseline'):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    for n in DOMAIN: v['z' + n] = lambda n=n: n
    v['zref'] = lambda: 'reference'
    def matches(actual, expected, names):
        return actual == tuple('other' if variant == name else value for value, name in zip(expected, names))
    v.update(aa=lambda p: p in ('person', 'learner', 'member', 'overlap') and not (variant == 'nonperson_learner' and p == 'learner'),
        si=lambda p, code, ref: variant != 'not_continuing_aid' and matches((p, symbol(code), code.rank, ref),
            ('person', 'so', 0, 'reference'), ('aid_person', 'aid_content', 'aid_rank', 'aid_reference')),
        hzwn=lambda p, role, ref: matches((p, role, ref), ('person', 'role', 'reference'),
            ('holder_person', 'holder_role', 'holder_reference')),
        hzwo=lambda role, code, ref: matches((role, symbol(code), code.rank, ref), ('role', 'so', 0, 'reference'),
            ('function_role', 'function_content', 'function_rank', 'function_reference')),
        hzwu=lambda role, code, ref: variant != 'not_principal' and matches((role, symbol(code), ref),
            ('role', 'so', 'reference'), ('principal_role', 'principal_content', 'principal_reference')),
        hzxf=lambda p, role, church, ref: variant != 'not_appointed' and matches((p, role, church, ref),
            ('person', 'role', 'church', 'reference'), ('appointment_person', 'appointment_role', 'appointment_church', 'appointment_reference')),
        hzxg=lambda role, code, church, ref: matches((role, symbol(code), code.rank, church, ref),
            ('role', 'hzxi', 0, 'church', 'reference'), ('duty_role', 'duty_content', 'duty_rank', 'duty_church', 'duty_reference')),
        h245x=lambda course, subject, ref: variant != 'not_introductory' and matches((course, subject, ref),
            ('course', 'subject', 'reference'), ('intro_course', 'intro_subject', 'intro_reference')),
        h245y=lambda course, ref: variant != 'not_question_answer' and matches((course, ref),
            ('course', 'reference'), ('form_course', 'form_reference')),
        h245z=lambda subject, ref: variant != 'nonreligious_subject' and matches((subject, ref),
            ('subject', 'reference'), ('religion_subject', 'religion_reference')))
    def pupils(teacher, role, church, learner, course, ref):
        return variant != 'empty' and learner in ('learner', 'overlap') and matches((teacher, role, church, course, ref),
            ('person', 'role', 'church', 'course', 'reference'),
            ('pupil_teacher', 'pupil_role', 'pupil_church', 'pupil_course', 'pupil_reference'))
    def care(person, role, congregation, church, code, ref):
        return matches((person, role, congregation, church, symbol(code), code.rank, ref),
            ('person', 'role', 'congregation', 'church', 'so', 0, 'reference'),
            ('care_person', 'care_role', 'care_group', 'care_church', 'care_content', 'care_rank', 'care_reference'))
    def membership(group, member, ref):
        return variant != 'empty' and member in ('member', 'overlap') and matches((group, ref),
            ('congregation', 'reference'), ('member_group', 'member_reference'))
    def recipients(audience, person, ref):
        if variant == 'empty': return False
        if ref != 'reference': return False
        students, members = {'learner', 'overlap'}, {'member', 'overlap'}
        if variant == 'missing_pupil': students.remove('overlap')
        if variant == 'missing_member': members.remove('overlap')
        if variant == 'extra_pupil': students.add('other')
        if variant == 'extra_member': members.add('other')
        if variant == 'swapped_ranges': students, members = members, students
        return person in (students if audience == 'students' else members if audience == 'members' else set())
    v.update(h246a=pupils, h246b=care, h246c=membership, h6t=recipients)
    return v


@lru_cache(None)
def role_checks():
    doc, rows = fixture('r35m'), {}
    for variant in ('baseline', 'not_continuing_aid', 'aid_person', 'aid_content', 'aid_reference',
        'holder_person', 'holder_role', 'holder_reference', 'function_role', 'function_content', 'function_reference',
        'not_principal', 'principal_role', 'not_appointed', 'appointment_person', 'appointment_role',
        'appointment_church', 'appointment_reference', 'duty_role', 'duty_content', 'duty_church', 'duty_reference'):
        v = model(doc, variant)
        assert v['dg'] is unknown
        actual = evaluate(doc, v, DOMAIN, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual); rows[variant] = actual[0]
    return dict(contrasts=rows, native_same_role_and_institution_witness=True, religious_service_not_executed=True)


@lru_cache(None)
def pupil_checks():
    rows = {}
    for target, variants in (
        ('r35n', ('baseline', 'not_introductory', 'not_question_answer', 'nonreligious_subject',
            'intro_course', 'intro_subject', 'intro_reference', 'form_course', 'form_reference', 'religion_subject', 'religion_reference')),
        ('r35o', ('baseline', 'nonperson_learner', 'not_question_answer', 'nonreligious_subject',
            'pupil_teacher', 'pupil_role', 'pupil_church', 'pupil_course', 'pupil_reference', 'form_course'))):
        doc = fixture(target); cases = {}
        for variant in variants:
            actual = evaluate(doc, model(doc, variant), DOMAIN, SCENES, True)
            assert actual == [variant == 'baseline'], (target, variant, actual); cases[variant] = actual[0]
        rows[target] = cases
    return dict(contrasts=rows, native_shared_course_and_subject=True, own_teacher_role_institution_preserved=True)


@lru_cache(None)
def audience_checks():
    doc, rows = fixture('r35q'), {}
    for variant in ('baseline', 'empty', 'missing_pupil', 'missing_member', 'extra_pupil', 'extra_member', 'swapped_ranges',
        'care_person', 'care_role', 'care_group', 'care_church', 'care_content', 'care_reference',
        'member_group', 'member_reference', 'pupil_teacher', 'pupil_role', 'pupil_church',
        'not_appointed', 'appointment_church', 'duty_church', 'not_question_answer', 'nonreligious_subject'):
        actual = evaluate(doc, model(doc, variant), DOMAIN, SCENES, True)
        assert actual == [variant in ('baseline', 'empty')], (variant, actual); rows[variant] = actual[0]
    return dict(contrasts=rows, native_complete_separate_ranges=True, overlapping_membership_allowed=True,
        empty_scope_not_mistaken_for_actual_teaching=True)


@lru_cache(None)
def unknown_checks():
    rows = []
    for target, name in (('r35m', 'hzxf'), ('r35m', 'hzxg'), ('r35n', 'h245x'), ('r35n', 'h245y'),
        ('r35n', 'h245z'), ('r35o', 'h246a'), ('r35q', 'h246b'), ('r35q', 'h246c'), ('r35q', 'h6t')):
        doc = fixture(target); v = model(doc); v[name] = unknown
        try: evaluate(doc, v, DOMAIN, SCENES, True)
        except ValueError as error: assert 'Unknown' in str(error), str(error)
        else: raise AssertionError(name)
        rows.append(name)
    return dict(unknown_inputs_refused=rows)


@lru_cache(None)
def structure_checks():
    new, old = catalog(), parent()
    assert not new.document['statements']
    for n, e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert e['declaration'] == old.entries[n]['declaration'] and e['meaning_ja'] == old.entries[n]['meaning_ja'], n
    validate_hashes(ROOT, read(PRIOR)['source_sha256'])
    validate_hashes(ROOT, {s['raw_archive']: s['raw_sha256'] for s in read(EVIDENCE)['sources']})
    for p, s in build().items(): assert (ROOT / p).read_text(encoding='utf-8') == s, p
    for notation in ('compact', 'full'):
        text = format_graph(new.document, notation); assert parse(text) == parse(transcribe(text, alphabet='v2')) == new.document
    return dict(new_definitions=len(MEANINGS), new_primitives=len(PRIMITIVES), inherited_meanings_preserved=True,
        active_manuscript_unchanged=True, new_semantic_reviews=0, archived_lexical_sources_verified=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p, s in build().items(): write_exact(ROOT / p, s)


def build_report():
    results = {}
    for name, fn in [('role', role_checks), ('pupils', pupil_checks), ('audiences', audience_checks),
                     ('unknown', unknown_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    paths = set(build()) | set(parent().source_sha256) | {DOC, PRIOR, EVIDENCE,
        'scripts/compose_clerical_audiences.py', 'scripts/check_clerical_audiences.py', 'tests/test_clerical_audiences.py',
        'scripts/compose_grounded_step.py', 'scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    return dict(status='same_clerical_role_and_complete_pupil_congregation_ranges', document=LIBRARY, **results,
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
