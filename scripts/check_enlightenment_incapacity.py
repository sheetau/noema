"""Check attainment methods, nonvacuous evaluation, and the guardian connection."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_enlightenment_incapacity import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, LIMITS, parent, build, closure,
)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_public_comparison_claim import seq
from scripts.check_scoped_counts import arithmetic
from scripts import check_public_reversal as prior

INDEX = 'data/semantic-review-index-v126.json'
AUDIT = 'data/enlightenment-incapacity-reading-v1.json'
REPORT = 'reports/enlightenment-incapacity-v1.json'
DOC = 'docs/enlightenment-incapacity-v1.md'
INVENTORY = prior.INVENTORY
PRIOR = prior.REPORT
PEOPLE = ('person', 'other', 'method', 'learning', 'public')
SCENES = ('reference', 'first', 'second', 'success', 'failure')
EXTRA = '''
r zperson[] a.r zreference[] d.r zgoal[] e.
r zcandidate[a d d] c.r zstable[a d d] c.r zopportunity[a d] c.
r zavailable[a a d] c.r zpossible[a a d d] c.r zselected[a a d d] c.
r zpublic[] a.
'''


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def boundary_document(roots, boundaries=()):
    doc = deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    doc.update(declarations=closure(doc, roots), statements=[])
    return doc


@lru_cache(None)
def fixture(source=False):
    doc = boundary_document(['r2mt' if source else 'r2ms'], ('up',) if source else ())
    args = 'k zperson[] k zreference[]' if source else (
        'k zperson[] k zgoal[] k zreference[] p zcandidate p zstable p zopportunity '
        'p zavailable p zpossible p zselected')
    return parse(format_graph(doc, 'compact') + EXTRA +
                 'q[k ' + ('r2mt' if source else 'r2ms') + '[' + args + ']].')


def model(doc, variant='baseline', successes=(False, False)):
    def available(p, method, point):
        return p == 'person' and point in ('first', 'second') and (
            method == 'method' and variant != 'no_available_method' or
            method == 'learning' and variant in ('learning_success', 'unassessed_learning'))

    def selected(p, method, point, result):
        if not available(p, method, point) or variant == 'empty_results':
            return False
        if method == 'learning':
            return variant != 'unassessed_learning' and result == 'success'
        passed = successes[point == 'second'] or variant == 'one_opportunity_success' and point == 'second'
        return result == ('success' if passed else 'failure')

    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    values.update(
        aa=lambda p: p == 'person' and variant != 'nonhuman',
        zperson=lambda: 'person', zreference=lambda: 'reference',
        zgoal=lambda: Content(SCENES, tuple(t == 'success' for t in SCENES)),
        zcandidate=lambda p, ref, t: (p, ref) == ('person', 'reference') and
            t in ('first', 'second') and variant != 'empty_profile',
        zstable=lambda p, ref, t: (p, ref) == ('person', 'reference') and
            not (variant == 'changed_baseline' and t == 'second'),
        zopportunity=lambda p, t: p == 'person' and
            not (variant == 'missing_opportunity' and t == 'second'),
        zavailable=available,
        zpossible=lambda p, m, t, r: available(p, m, t) and r in ('success', 'failure') and
            not (variant == 'impossible_selected_result' and r == 'failure'),
        zselected=selected,
    )
    values.update(
        up=lambda p: Content(SCENES, tuple(p == 'person' and t == 'success' for t in SCENES)),
        h223p=lambda p, d, ref, t: symbol(d) == 'up' and values['zcandidate'](p, ref, t),
        h223q=lambda p, d, ref, t: symbol(d) == 'up' and values['zstable'](p, ref, t),
        h223r=lambda p, d, t: symbol(d) == 'up' and values['zopportunity'](p, t),
        ae=available, af=values['zpossible'], ap=selected,
    )
    if variant == 'wrong_goal_profile':
        values['h223p'] = lambda p, d, ref, t: symbol(d) == 'bb'
    if variant == 'wrong_person_profile':
        values['h223p'] = lambda p, d, ref, t: p == 'other'
    if variant == 'wrong_reference_profile':
        values['h223p'] = lambda p, d, ref, t: ref == 'success'
    return values


@lru_cache(None)
def capacity_checks():
    doc = fixture()
    combinations = []
    for successes in product((False, True), repeat=2):
        actual = evaluate(doc, model(doc, successes=successes), PEOPLE, SCENES, True)
        assert actual == [not any(successes)], (successes, actual)
        combinations.append(dict(successes=list(successes), incapable=actual[0]))
    positives = ('baseline', 'no_available_method')
    negatives = ('learning_success', 'one_opportunity_success', 'empty_profile', 'changed_baseline',
                 'missing_opportunity', 'empty_results', 'impossible_selected_result',
                 'unassessed_learning', 'nonhuman')
    rows = {}
    for variant in (*positives, *negatives):
        actual = evaluate(doc, model(doc, variant), PEOPLE, SCENES, True)
        assert actual == [variant in positives], (variant, actual)
        rows[variant] = actual
    for name in ('zcandidate', 'zstable', 'zopportunity', 'zavailable', 'zpossible', 'zselected', 'zgoal'):
        values = model(doc)
        values[name] = unknown
        try:
            evaluate(doc, values, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(combinations=combinations, contrasts=rows, unknown_inputs_refused=7,
                acquisition_methods_not_filtered_out=True, all_opportunities_not_one_failure=True)


@lru_cache(None)
def source_checks():
    doc = fixture(True)
    rows = {}
    for variant in ('baseline', 'learning_success', 'one_opportunity_success',
                    'wrong_goal_profile', 'wrong_person_profile', 'wrong_reference_profile',
                    'empty_profile', 'unassessed_learning'):
        actual = evaluate(doc, model(doc, variant), PEOPLE, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    # Goal state at each result is a declared boundary, not an opaque replacement
    # of the method/profile calculation being tested here.
    assert 'rqvo' not in {d['name'] for d in doc['declarations']}
    for name in ('h223p', 'h223q', 'h223r'):
        values = model(doc)
        values[name] = unknown
        try:
            evaluate(doc, values, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(contrasts=rows, goal_is_existing_up=True, up_content_is_explicit_boundary=True,
                unknown_acquisition_inputs_refused=3,
                current_exercise_incapacity_not_used_as_acquisition_incapacity=True)


@lru_cache(None)
def role_checks():
    doc = boundary_document(['r2mu'])
    doc = parse(format_graph(doc, 'compact') + EXTRA +
                'q[k r2mu[k zperson[] k zpublic[] k zreference[]]].')
    rows = {}
    for variant in ('baseline', 'no_supervisory_role', 'self_only', 'wrong_public',
                    'duplicate_members', 'nonhuman_member', 'nonhuman_guardian'):
        members = {'self_only': ('person',), 'wrong_public': ('method',),
                   'duplicate_members': ('other', 'other'), 'nonhuman_member': ('method',)}.get(
                       variant, ('person', 'other'))
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        values.update(arithmetic())
        values.update(zperson=lambda: 'person', zpublic=lambda: 'public', zreference=lambda: 'reference',
                      aa=lambda p: p in ('person', 'other') and not (
                          variant == 'nonhuman_guardian' and p == 'person'),
                      mp=lambda group: seq(members) if group == 'public' else seq(()),
                      dc=lambda actor, target, point:
                          (actor, target, point) == ('person', 'person' if variant == 'self_only' else 'other',
                                                     'reference') and variant != 'no_supervisory_role')
        actual = evaluate(doc, values, PEOPLE, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, no_appointment_or_actual_enlightenment_inferred=True)


@lru_cache(None)
def integration_checks():
    doc = boundary_document(['r2mv'], ('bf', 'up'))
    args = prior.ARGS['r2mr'].replace(' p zrole p zincapable', '')
    doc = parse(format_graph(doc, 'compact') + prior.EXTRA + 'q[k r2mv[' + args + ']].')
    rows = {}
    for variant in ('baseline', 'no_pressure', 'learnable_agitator_without_pressure',
                    'no_prior_role', 'overlapping_cohorts', 'only_one_former_pressured'):
        inherited = 'no_pressure' if variant == 'learnable_agitator_without_pressure' else (
            'former_not_guardian' if variant == 'no_prior_role' else variant)
        values = prior.model(doc, inherited)
        role = values['zrole']
        values.update(
            dc=lambda person, target, point: target == 'p' and role(person, 'public', point),
            up=lambda p: Content(prior.SCENES, tuple(
                variant == 'learnable_agitator_without_pressure' and p == 'j' and t == 'last'
                for t in prior.SCENES)),
            h223p=lambda p, desc, ref, point: symbol(desc) == 'up' and point == 'incited',
            h223q=lambda p, desc, ref, point: symbol(desc) == 'up',
            h223r=lambda p, desc, point: symbol(desc) == 'up',
            ae=lambda p, m, point: (p, m, point) == ('j', 'prioract', 'incited'),
            af=lambda p, m, point, end: (p, m, point, end) == ('j', 'prioract', 'incited', 'last'),
            ap=lambda p, m, point, end: (p, m, point, end) == ('j', 'prioract', 'incited', 'last'),
        )
        actual = evaluate(doc, values, prior.PEOPLE, prior.SCENES, True)
        expected = variant in ('baseline', 'learnable_agitator_without_pressure', 'overlapping_cohorts')
        assert actual == [expected], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, role_and_incapacity_functions_filled=True,
                native_reversal_retention_and_method_checks_executed=True,
                incitation_relation_still_explicit_boundary=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    phrase = 'einigen seiner Vormünder, die selbst aller Aufklärung unfähig sind'
    start = unit['text'].index(phrase)
    return dict(status='guardian_role_and_enlightenment_incapacity_partial',
                document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[start, start + len(phrase)], text=phrase),
                interpretation=LIMITS, whole_sentence_semantically_verified=False,
                newly_reviewed_sentence_characters=0, preserved_first_two_sentence_characters=382,
                primary_source='https://korpora.org/Kant/aa08/036.html',
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in (FULL, BASIS, DOC, INVENTORY, PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'] == old.document['statements'] and len(new.document['statements']) == 59
    assert new.document['declarations'][:len(old.document['declarations'])] == old.document['declarations']
    assert all(new.entries[n] == e for n, e in old.entries.items())
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path, indices in prior.SENTENCES:
        record = read(path)
        assert record['selection'] == selection_binding(new, indices)
        validate_hashes(ROOT, record['source_sha256'])
    validate_hashes(ROOT, read(PRIOR)['source_sha256'])
    assert read(AUDIT) == reading()
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(new_definitions=len(MEANINGS), new_primitives=3, preserved_statements=59,
                preserved_reviews=len(reviews), preserved_sentence_characters=382, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('capacity', capacity_checks), ('source', source_checks), ('roles', role_checks),
                     ('integration', integration_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, PRIOR, *[p for p, _ in prior.SENTENCES],
        'scripts/compose_enlightenment_incapacity.py', 'scripts/check_enlightenment_incapacity.py',
        'tests/test_enlightenment_incapacity.py', 'scripts/check_public_reversal.py',
        'scripts/compose_public_reversal.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py', 'scripts/check_public_comparison_claim.py', 'scripts/check_scoped_counts.py',
    }
    return dict(status='enlightenment_incapacity_third_sentence_partial', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='partial_guardian_role_and_attainment_incapacity'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
