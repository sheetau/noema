import json

import pytest

from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_bounded_hindrance import REPORT, build_report
from scripts.compose_bounded_hindrance import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_intervention_results_match_independent_enumeration(result):
    assert result['finite']['binary_table_score_tolerance_cases'] == 320
    rows = result['finite']['contrasts']
    assert rows['large_loss'] == rows['below_boundary'] == [True, False, True, False]
    assert rows['exact_boundary'] == [True, True, False, True]


def test_no_solution_or_missing_factor_is_not_vacuous_no_harm(result):
    rows = result['finite']['contrasts']
    for name in ('no_solutions', 'no_on_solutions', 'no_off_solutions'):
        assert rows[name] == [False] * 4
    assert rows['negative_tolerance'] == [True, False, False, False]
    for name in ('empty', 'factor_absent', 'duplicate'):
        assert result['finite']['scope_cases'][name] == [False] * 4


def test_acceptable_possible_pair_does_not_imply_all_pairs_are_acceptable(result):
    assert result['finite']['contrasts']['multiple_mixed'] == [True, True, True, False]


def test_bounded_harm_does_not_assert_actual_growth(result):
    for name in ('small_loss_while_both_progress', 'no_progress_on_either_side', 'regression_but_bounded', 'improvement'):
        assert result['finite']['contrasts'][name] == [True, True, False, True]
    assert result['source']['contrasts']['no_progress'] == [True, True, True]


def test_comparison_uses_matching_units_and_only_declared_causal_variables(result):
    rows = result['finite']['contrasts']
    assert rows['shifted_origin'] == rows['scaled_with_tolerance'] == [True, True, False, True]
    assert rows['scaled_without_tolerance'] == [True, False, True, False]
    assert result['finite']['scope_cases']['sixteen_individuals_two_variables'] == [True, True, False, True]


def test_the_intervention_factor_must_correspond_to_the_same_policy(result):
    rows = result['source']['contrasts']
    assert rows['baseline'] == [True, True, True]
    for name in ('wrong_worlds', 'opposite_policy', 'unrelated_policy', 'no_solution'):
        assert rows[name] == [False, False, True]
    assert rows['large_harm'] == rows['not_actual'] == [True, False, True]
    assert rows['not_permitted'] == [True, True, False]


def test_qualified_frequency_policy_can_be_described_without_evaluation(result):
    assert result['source']['permission_does_not_evaluate_policy_or_comparison']
    assert result['source']['unknown_score_and_policy_refused']
    assert result['source']['qualified_policy_description_roundtrips']
    assert result['source']['nested_frequency_target_typechecked_without_evaluation']
    assert not result['source']['progress_measure_grounding_complete']


def test_existing_scoped_interventions_and_author_claims_are_retained():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    text, basis = source_composed()
    doc = parse(text)
    audit = audit_basis(doc, basis)
    assert (audit['primitive_count'], audit['definition_count']) == (250, 474)
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['statements']) == 15


def test_report_reproduces_without_promoting_interpretive_conditions_to_equivalence(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert result['parent_and_scoped_library_preserved'] and result['roundtrips']
    assert result['new_primitives'] == result['new_source_assertions'] == 0
    assert result['alignment']['semantic_completion'] is False
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
