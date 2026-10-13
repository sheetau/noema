import json

import pytest

from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_qualified_few import build_report, REPORT
from scripts.compose_qualified_few import ROOT, PARENT, generic_composed, source_composed


@pytest.fixture(scope='module')
def result():
    # Reuse the expensive native interpretation across semantic contrasts.
    # This is the executed report builder, not a read of the saved answers.
    return build_report()


def test_positive_witnesses_and_complete_negative_assessment_are_distinct(result):
    generic = result['generic']
    assert generic['truth_and_threshold_cases'] == 256
    assert generic['permutation_cases'] == 6
    assert generic['contrasts']['unassessed_positive'] == [True] * 3
    assert generic['contrasts']['unassessed_negative'] == [False] * 3


def test_having_once_achieved_independence_does_not_justify_a_negative_combined_classification(result):
    rows = result['source_cases']['cases']
    assert rows['known_achievement_unassessed_earlier'] == [True, False, False, False]
    assert rows['unassessed_after_positive'] == [True] * 4
    assert rows['exercise_before_achievement'] == [True, True, True, False]


def test_missing_expectations_do_not_remove_an_actual_successful_person(result):
    rows = result['concession_cases']
    assert rows['baseline'] == [True, True]
    assert rows['no_expectations'] == rows['expected_also_exercises'] == [True, False]
    assert result['source_cases']['cases']['unknown_expectations'] == [True] * 4


def test_unknown_support_is_not_converted_into_an_unsuccessful_person(result):
    assert result['source_cases']['unknown_support_refused']


def test_successful_people_cannot_be_counted_in_an_incomplete_or_duplicated_population(result):
    rows = result['generic']['contrasts']
    for name in ('omitted_nonqualifier', 'duplicate', 'empty_scope_list'):
        assert rows[name] == [True, False, False]
    assert result['source_cases']['cases']['omitted_person'] == [True, True, False, False]


def test_zero_and_upper_boundary_are_distinct_from_positive_few(result):
    assert result['generic']['contrasts']['zero_qualifiers'] == [True, True, False]
    assert result['generic']['contrasts']['at_upper_boundary'] == [True, False, False]
    assert result['source_cases']['cases']['no_exercise'] == [True, True, True, False]


def test_author_inference_does_not_execute_the_quoted_population_claim(result):
    discourse = result['discourse_cases']
    assert len(discourse['cases']) == 9
    assert [name for name, row in discourse['cases'].items() if row == [True]] == ['baseline']
    assert discourse['all_count_and_content_primitives_guarded_against_execution']


def test_unbounded_population_exists_is_not_verified_by_enumerating_a_few_sequences(result):
    assert result['unbounded_sequence']['refused']
    assert 'unbounded sequence' in result['unbounded_sequence']['reason']
    assert not result['alignment']['full_semantic_equivalence']
    assert result['alignment']['source'].startswith('Daher giebt es nur Wenige,')
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}


def test_prior_source_is_preserved_and_the_new_reference_is_a_discourse_node():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    for builder, expected in ((generic_composed, (4, 14)), (source_composed, (224, 365))):
        text, basis = builder()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == expected
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'][:-1] == parent['statements']
    assert doc['statements'][-1]['body']['symbol'] == 'h5u'
    assert len(doc['statements']) == 15


def test_saved_report_reproduces_from_current_sources(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
