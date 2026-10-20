"""Evaluate native intervention solutions, qualitative order and question scope."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import SequenceValue, evaluate_document
from noema.meaning_catalog import load_catalog
from noema.script import transcribe
from noema.semantic_reviews import digest, validate_hashes
from scripts.compose_qualitative_influence import ROOT, LIBRARY, BASIS, PARENT_BASIS, MEANINGS, LIMITS, build, parent
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

REPORT = 'reports/qualitative-influence-v1.json'
DOC = 'docs/qualitative-influence-v1.md'
PEOPLE = ('factor', 'result', 'outside')
STATES = tuple(product((False, True), repeat=2))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture():
    extra = '''r zvariables[] j[a].r zequation[a h[a] c] c.r zfactor[] a.
r zassessed[h[a] c] c.r zatleast[h[a] c h[a] c] c.'''
    args = 'k zvariables[] p zequation k zfactor[]'
    queries = ''
    for name in ('r2vd', 'r2ve', 'r2vf', 'r2vg', 'r2vh', 'r2vi'):
        tail = ' p zatleast' if name in ('r2ve', 'r2vf') else ' p zassessed p zatleast'
        queries += 'q[k ' + name + '[' + args + tail + ']].'
    return parse((ROOT / LIBRARY).read_text(encoding='utf-8') + extra + queries)


def state_key(state):
    return (bool(state('factor')), bool(state('result')))


def model(table, grades, *, assessed=None, relation=None, variables=('factor', 'result'), factor='factor'):
    """The factor equation is replaced by intervention; the outcome mechanism stays fixed."""
    def equation(variable, state):
        if variable == 'result':
            return table[STATES.index(state_key(state))]
        return False
    return dict(zvariables=lambda: SequenceValue(variables, '"individual"'),
                zfactor=lambda: factor, zequation=equation,
                zassessed=lambda state: assessed is None or state_key(state) in assessed,
                zatleast=lambda left, right: (state_key(left), state_key(right)) in relation if relation is not None
                    else grades[STATES.index(state_key(left))] >= grades[STATES.index(state_key(right))])


def reference(table, grades):
    solutions = {sign: [i for i, (f, output) in enumerate(STATES)
                        if f == sign and table[i] == output] for sign in (False, True)}
    pairs = list(product(solutions[True], solutions[False]))
    valid = bool(solutions[True]) and bool(solutions[False])
    decrease = any(grades[on] < grades[off] for on, off in pairs)
    increase = any(grades[on] > grades[off] for on, off in pairs)
    return [valid, decrease, increase, valid and decrease, valid and not decrease,
            valid and not decrease and increase]


@lru_cache(None)
def mechanism_checks():
    doc = fixture()
    count = 0
    patterns = set()
    # All two-variable outcome mechanisms, including inconsistent and multistable ones.
    # Binary grades suffice here to exhaustively vary equality and direction independently.
    for table in product((False, True), repeat=4):
        for grades in product((0, 1), repeat=4):
            actual = evaluate(doc, model(table, grades), PEOPLE, ('reference',), True)
            expected = reference(table, grades)
            assert actual == expected, (table, grades, actual, expected)
            patterns.add(tuple(actual))
            count += 1
    rows = {}
    table = tuple(s[1] for s in STATES)  # Both outcomes solve each intervention.
    for name, grades, expected in (
        ('equal_only', (1, 1, 1, 1), [True, False, False, False, True, False]),
        ('gain_with_ties', (0, 1, 1, 2), [True, False, True, False, True, True]),
        ('loss_with_ties', (1, 2, 0, 1), [True, True, False, True, False, False]),
        ('mixed_effects', (0, 2, 1, 1), [True, True, True, True, False, False]),
    ):
        actual = evaluate(doc, model(table, grades), PEOPLE, ('reference',), True)
        assert actual == expected, (name, actual)
        rows[name] = actual
    return dict(exhaustive_mechanism_grade_combinations=count, distinct_profiles=len(patterns),
                contrasts=rows, native_intervention_solutions_evaluated=True,
                same_equations_and_factor_on_both_sides=True,
                columns=['valid', 'raw_decrease', 'raw_increase', 'assessed_decrease', 'nondecrease', 'nondecrease_with_gain'])


@lru_cache(None)
def guard_checks():
    doc = fixture()
    table = tuple(s[1] for s in STATES)
    grades = (0, 1, 1, 2)
    ge = {(a, b) for i, a in enumerate(STATES) for j, b in enumerate(STATES) if grades[i] >= grades[j]}
    # A cyclic comparison is total and reflexive, but is not transitive.
    cyclic = {(s, s) for s in STATES} | {(STATES[0], STATES[1]), (STATES[1], STATES[2]),
        (STATES[2], STATES[0]), (STATES[3], STATES[0]), (STATES[3], STATES[1]), (STATES[3], STATES[2])}
    cases = {
        'missing_assessment': dict(assessed=set(STATES) - {STATES[3]}),
        'not_reflexive': dict(relation=ge - {(STATES[1], STATES[1])}),
        'cyclic_comparison': dict(relation=cyclic),
        'incomparable_cross_sides': dict(relation={(s, s) for s in STATES}),
        'empty_variables': dict(variables=()),
        'duplicate_variables': dict(variables=('factor', 'result', 'result')),
        'factor_outside_variables': dict(factor='outside'),
    }
    rows = {}
    for name, kwargs in cases.items():
        actual = evaluate(doc, model(table, grades, **kwargs), PEOPLE, ('reference',), True)
        assert not any(actual[i] for i in (0, 3, 4, 5)), (name, actual)
        rows[name] = actual
    # Unassessed states that do not solve either intervention must not contaminate the profile.
    deterministic = (False, False, True, True)
    actual = evaluate(doc, model(deterministic, grades, assessed={STATES[0], STATES[3]}), PEOPLE, ('reference',), True)
    assert actual == [True, False, True, False, True, True], actual
    rows['unassessed_nonsolutions'] = actual
    for name in ('zequation', 'zassessed', 'zatleast'):
        values = model(table, grades)
        values[name] = unknown
        try:
            evaluate(doc, values, PEOPLE, ('reference',), True)
        except ValueError as error:
            assert 'Unknown' in str(error), (name, error)
        else:
            raise AssertionError('Unknown interpretation treated as a negative result: ' + name)
    return dict(contrasts=rows, unknown_inputs_refused=3, missing_or_invalid_evidence_not_nonhindrance=True)


@lru_cache(None)
def question_checks():
    # Pure answer-set construction: no assertion that an answer exists.
    from scripts.compose_grounded_step import closure
    doc = deepcopy(catalog().document)
    doc.update(declarations=closure(doc, ['r2vj', 'r2vk']), statements=[])
    doc = parse(format_graph(doc, 'compact') + '''
r zscope[a] c.r zchecked[a] c.r zloss[a] c.r zgain[a] c.
q[k r2vj[p zscope p zchecked p zloss]].
q[k r2vk[p zscope p zchecked p zloss p zgain]].
''')
    people = ('harm', 'help', 'neutral', 'mixed', 'unassessed', 'outside')
    effects = {'harm': (True, False), 'help': (False, True), 'neutral': (False, False),
               'mixed': (True, True), 'unassessed': (False, True), 'outside': (False, True)}
    def values(scope):
        return dict(zscope=lambda item: item in scope, zchecked=lambda item: item != 'unassessed',
                    zloss=lambda item: effects[item][0], zgain=lambda item: effects[item][1])
    def run(scope):
        return evaluate_document(doc, individuals=people, situations=('reference',), primitives=values(scope))
    questions = run(set(people) - {'outside'})
    answers = [[row[0] for row in question['answers']] for question in questions]
    assert answers == [['harm', 'mixed'], ['help']], answers
    empty = run(set())
    assert all(question['answers'] == [] for question in empty)
    # Predicates are open, same-person functions; no copying another candidate's gain.
    return dict(answer_sets=answers, empty_scope_has_no_forced_answer=True,
                same_candidate_across_scope_assessment_loss_and_gain=True,
                question_kind='individual_answer_question')


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    record = json.loads((ROOT / BASIS).read_text(encoding='utf-8'))
    for name in record['imported_symbols']:
        for key in ('kind', 'declaration', 'meaning_ja'):
            assert new.entries[name][key] == old.entries[name][key], (name, key)
    assert not new.document['statements']
    assert not [new.entries[n] for n in MEANINGS if new.entries[n]['kind'] == 'primitive']
    validate_hashes(ROOT, record['import_source_sha256'])
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body, path
    for notation in ('compact', 'full'):
        text = format_graph(new.document, notation)
        assert parse(text) == parse(transcribe(text, alphabet='v2')) == new.document
    return dict(imported_declarations_and_meanings_preserved=len(record['imported_symbols']),
                added_definitions=len(MEANINGS), added_primitives=0, added_author_statements=0,
                new_semantically_reviewed_characters=0, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items():
        write_exact(ROOT / path, body)


def build_report():
    results = {}
    for name, fn in [('mechanisms', mechanism_checks), ('guards', guard_checks),
                     ('questions', question_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = {LIBRARY, BASIS, DOC, PARENT_BASIS, parent().document_path,
             'scripts/compose_qualitative_influence.py', 'scripts/check_qualitative_influence.py',
             'tests/test_qualitative_influence.py', 'scripts/check_pastoral_roles.py',
             'scripts/check_motive_causes.py'}
    return dict(status='partial_qualitative_influence_and_question_core_checked',
                document=LIBRARY, **results, limitations=LIMITS,
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
