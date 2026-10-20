"""Check demand presence, complete withdrawal and fixed goal bindings separately."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, validate_hashes
from noema.script import transcribe
from scripts.compose_aligned_influence import (
    ROOT, LIBRARY, BASIS, PARENT_BASIS, PROFILE_BASIS, PROFILE_LIBRARY,
    MEANINGS, LIMITS, parent, profile, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

REPORT = 'reports/aligned-restriction-influence-v1.json'
DOC = 'docs/aligned-restriction-influence-v1.md'
PEOPLE = ('first', 'second', 'factor', 'outcome', 'source', 'person', 'role', 'activity', 'other', 'public')
SCENES = ('reference', 'on', 'off', 'partial', 'choice')
FIELDS = 'p zrecords p zsource p zperson p zrole p zactivity p zcode p zpolarity'
MODEL = 'k zvariables[] p zequation k zfactor[] p zworld'
TARGET = 'k zpublic[] k zreference[] p zevaluated p zatleast'
WHOLE = FIELDS + ' p zrequired ' + MODEL + ' p zchoices ' + TARGET
EXTRA = '''
r zrecords[a] c.r zsource[a] a.r zperson[a] a.r zrole[a] a.r zactivity[a] a.
r zpolarity[a] c.r ztruth[a a d] c.
d zbase[person a activity a] e[b point[k ztruth[v person v activity v point]]].
d zinner[] i[h[a a] e][r[p zbase]].
d zcontent[person a activity a] e[c[s[k zinner[]]][v person v activity]].
d zcode[record a] i b[h[a a] e][r b[p zcontent]].
r zrequired[a a a a i b[h[a a] e] c d] c.r zchoices[a d] c.
r zvariables[] j[a].r zequation[a h[a] c] c.r zfactor[] a.
r zworld[h[a] c] d.r zpublic[] a.r zreference[] d.
r zevaluated[a d i b[h[a d] e] d] c.
r zatleast[a d i b[h[a d] e] d d] c.
'''


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind):
    roots = {
        'demands': ['r2vl', 'r2vm'],
        'alignment': ['r2vp'],
        'target': ['r2vq'],
        'combined': ['r2vr', 'r2vs', 'r2vt', 'r2vu'],
    }[kind]
    doc = deepcopy(catalog().document)
    doc.update(declarations=closure(doc, roots), statements=[])
    queries = {
        'demands': ('q[k r2vl[' + FIELDS + ' p zrequired e[n p a b][n p a b] k zreference[]]].'
                    'q[k r2vl[' + FIELDS + ' p zrequired u[e[n p a b][n p a b]] k zreference[]]].'
                    'q[k r2vm[' + FIELDS + ' p zchoices]].'),
        'alignment': 'q[k r2vp[' + FIELDS + ' p zrequired ' + MODEL + ']].',
        'target': 'q[k r2vq[' + MODEL + ' ' + TARGET + ']].',
        'combined': ''.join('q[k ' + n + '[' + WHOLE + ']].' for n in
                            ('r2vr', 'r2vs', 'r2vt', 'r2vu')),
    }[kind]
    return parse(format_graph(doc, 'compact') + EXTRA + queries)


def model(doc, variant='baseline', *, present=(True, True), fulfills=(False, True), direction='gain'):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    v.update(zrecords=lambda item: variant != 'empty_records' and item in ('first', 'second'),
             zsource=lambda item: 'source', zperson=lambda item: 'person', zrole=lambda item: 'role',
             zactivity=lambda item: 'activity' if item == 'first' else 'other',
             zpolarity=lambda item: item == 'first',
             zchoices=lambda item, point: variant != 'no_choices' and (
                 item, point) == ('other' if variant == 'outside_record_choice' else 'first', 'choice'),
             zvariables=lambda: SequenceValue(('factor', 'outcome'), '"individual"'),
             zfactor=lambda: 'factor', zpublic=lambda: 'public', zreference=lambda: 'reference')

    def truth(person, activity, point):
        if (person, point) != ('person', 'choice'):
            return variant == 'actual_compliance'
        if activity == 'activity':
            return True if variant == 'all_choices_comply' else fulfills[0]
        return fulfills[1]

    def required(source, person, role, activity, code, polarity, point):
        expected = ('other' if variant == 'wrong_source' else 'source',
                    'other' if variant == 'wrong_person' else 'person',
                    'other' if variant == 'wrong_role' else 'role')
        if code.rank != 1 or (source, person, role) != expected or symbol(code) != (
                'othercontent' if variant == 'wrong_code' else 'zcontent'):
            return False
        if (activity, polarity) not in (('activity', True), ('other', False)):
            return False
        index = int(activity == 'other')
        if point == 'reference':
            return present[index]
        return point == 'on' or point == 'partial' and index == 0

    def world(state):
        flag = state('factor')
        if variant == 'reversed_policy':
            flag = not flag
        if variant == 'partly_withdrawn' and not flag or variant == 'partly_applied' and flag:
            return 'partial'
        if variant == 'compliance_as_policy':
            return 'reference'
        return 'on' if flag else 'off'

    def target(public, reference, goal):
        return (public, reference, goal.rank, symbol(goal)) == (
            'other' if variant == 'other_public' else 'public',
            'off' if variant == 'other_reference' else 'reference', 1,
            'bi' if variant == 'other_goal' else 'r2ln')

    def evaluated(public, reference, goal, point):
        return target(public, reference, goal) and point in ('on', 'off') and not (
            variant == 'unassessed_on' and point == 'on')

    def atleast(public, reference, goal, first, second):
        if not target(public, reference, goal):
            return False
        grades = {'on': 2 if direction == 'gain' else 0 if direction == 'loss' else 1,
                  'off': 1, 'partial': 1, 'reference': 1, 'choice': 1}
        if variant == 'comparison_other_worlds' and (first == 'on' or second == 'on'):
            return False
        return grades[first] >= grades[second]

    v.update(ztruth=truth, zrequired=required, zworld=world,
             zequation=lambda variable, state: variable == 'outcome' and state('factor'),
             zevaluated=evaluated, zatleast=atleast)
    return v


@lru_cache(None)
def demand_checks():
    doc = fixture('demands')
    rows = []
    for present, fulfills in product(product((False, True), repeat=2), repeat=2):
        actual = evaluate(doc, model(doc, present=present, fulfills=fulfills), PEOPLE, SCENES, True)
        wanted = [all(present), not any(present), not fulfills[0]]
        assert actual == wanted, (present, fulfills, actual)
        rows.append(dict(requirements=present, content_truths=fulfills, result=actual))
    contrasts = {}
    for name in ('wrong_source', 'wrong_person', 'wrong_role', 'wrong_code',
                 'empty_records', 'no_choices', 'outside_record_choice', 'all_choices_comply'):
        actual = evaluate(doc, model(doc, name), PEOPLE, SCENES, True)
        expected = [False, True, True] if name.startswith('wrong_') else (
            [False, False, False] if name == 'empty_records' else [True, False, False])
        assert actual == expected, (name, actual, expected)
        contrasts[name] = actual
    # The content body actually disquotes a native rank-zero function. Its outer
    # description therefore needs rank one; a low-rank copy must be rejected.
    low_rank = deepcopy(doc)
    low_rank.update(declarations=closure(doc, ['zcontent']), statements=[])
    malformed = format_graph(low_rank, 'compact') + 'd zbad[] i[h[a a] e][r[p zcontent]].'
    try:
        parse(malformed)
    except ValueError:
        low_rank_refused = True
    else:
        raise AssertionError('A rank-zero quote accepted the content disquotation')
    return dict(presence_content_combinations=rows, contrasts=contrasts,
                absence_requires_all_records_absent=True, demands_do_not_assert_fulfillment=True,
                native_closed_content_descriptions_evaluated=True,
                rank_one_content_kept=True, lower_rank_quote_refused=low_rank_refused)


@lru_cache(None)
def alignment_checks():
    doc = fixture('alignment')
    rows = {}
    for name in ('baseline', 'actual_compliance', 'partly_withdrawn', 'partly_applied',
                 'reversed_policy', 'compliance_as_policy', 'wrong_source',
                 'wrong_person', 'wrong_role', 'wrong_code', 'empty_records'):
        actual = evaluate(doc, model(doc, name), PEOPLE, SCENES, True)
        assert actual == [name in ('baseline', 'actual_compliance')], (name, actual)
        rows[name] = actual
    values = model(doc)
    values['ztruth'] = unknown
    assert evaluate(doc, values, PEOPLE, SCENES, True) == [True]
    for primitive in ('zrequired', 'zworld', 'zequation'):
        values = model(doc)
        values[primitive] = unknown
        try:
            evaluate(doc, values, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error), error
        else:
            raise AssertionError(primitive)
    return dict(contrasts=rows, partial_withdrawal_rejected=True,
                fulfillment_not_executed_for_policy_alignment=True, unknown_inputs_refused=3)


@lru_cache(None)
def target_checks():
    doc = fixture('target')
    rows = {}
    for name in ('baseline', 'other_public', 'other_reference', 'other_goal',
                 'unassessed_on', 'comparison_other_worlds'):
        actual = evaluate(doc, model(doc, name), PEOPLE, SCENES, True)
        assert actual == [name == 'baseline'], (name, actual)
        rows[name] = actual
    # Imported primitives of r2ln remain unknown: only its typed description is passed.
    return dict(contrasts=rows, same_public_reference_goal_and_world_mapping=True,
                enlightenment_goal_not_executed=True)


@lru_cache(None)
def combined_checks():
    doc = fixture('combined')
    rows = {}
    for direction, wanted in [('loss', [True, True, False, False]),
                              ('equal', [True, False, True, False]),
                              ('gain', [True, False, True, True])]:
        actual = evaluate(doc, model(doc, direction=direction), PEOPLE, SCENES, True)
        assert actual == wanted, (direction, actual)
        rows[direction] = actual
    for name in ('partly_withdrawn', 'all_choices_comply', 'other_goal', 'unassessed_on'):
        actual = evaluate(doc, model(doc, name), PEOPLE, SCENES, True)
        assert actual == [False] * 4, (name, actual)
        rows[name] = actual
    return dict(contrasts=rows, native_demand_alignment_and_comparison_composed=True,
                semantic_boundaries=['qualitative progress interpretation is supplied relative to r2ln; its truth is not evaluated'],
                original_two_questions_completed=False)


@lru_cache(None)
def structure_checks():
    old, prior, new = parent(), profile(), catalog()
    data = json.loads((ROOT / BASIS).read_text(encoding='utf-8'))
    for name in data['imported_symbols']:
        origin = prior.entries[name] if name in prior.entries else old.entries[name]
        for key in ('kind', 'declaration', 'meaning_ja'):
            assert new.entries[name][key] == origin[key], (name, key)
    validate_hashes(ROOT, data['import_source_sha256'])
    validate_hashes(ROOT, json.loads((ROOT / 'reports/qualitative-influence-v1.json').read_text(encoding='utf-8'))['source_sha256'])
    assert not new.document['statements']
    assert all(new.entries[n]['kind'] == 'definition' for n in MEANINGS)
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body, path
    for notation in ('compact', 'full'):
        text = format_graph(new.document, notation)
        assert parse(text) == parse(transcribe(text, alphabet='v2')) == new.document
    return dict(imported_declarations_and_meanings_preserved=len(data['imported_symbols']),
                added_definitions=len(MEANINGS), added_primitives=0,
                added_author_statements=0, new_semantically_reviewed_characters=0, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items():
        write_exact(ROOT / path, body)


def build_report():
    checks = {}
    for name, fn in [('demands', demand_checks), ('alignment', alignment_checks), ('target', target_checks),
                     ('combined', combined_checks), ('structure', structure_checks)]:
        checks[name] = fn()
        print(name + ' checked', flush=True)
    record = json.loads((ROOT / BASIS).read_text(encoding='utf-8'))
    paths = set(record['import_source_sha256']) | {LIBRARY, BASIS, DOC,
        'reports/qualitative-influence-v1.json', 'scripts/compose_aligned_influence.py',
        'scripts/check_aligned_influence.py', 'tests/test_aligned_influence.py',
        'scripts/compose_qualitative_influence.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py'}
    return dict(status='partial_aligned_demand_and_enlightenment_influence_checked',
                document=LIBRARY, **checks, limitations=LIMITS,
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
