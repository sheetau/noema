import json

import pytest

from noema.grammar import parse
from scripts.check_parameterized_goals import REPORT, build_report
from scripts.compose_parameterized_goals import ROOT, PARENT


@pytest.fixture(scope='module')
def result(): return build_report()


def test_bound_purpose_does_not_require_achievement(result):
    for row in result['generic']['cases']:
        aimed, solemnity = row['aimed'], row['solemnity']
        assert row['results'] == [aimed, aimed, aimed and solemnity]
    assert result['generic']['goal_truth_not_executed']
    assert result['source']['goal_truth_not_executed']


def test_template_arguments_and_action_witness_cannot_be_swapped(result):
    assert len(result['generic']['contrasts']) == 6
    assert all(row == [False] * 3 for row in result['generic']['contrasts'].values())
    assert len(result['source']['contrasts']) == 8
    assert all(row == [False] for row in result['source']['contrasts'].values())
    for row in result['source']['cases']:
        assert row['results'] == [row['aimed'] and row['solemnity']]


def test_causal_result_requires_the_same_template_bindings_and_actual_truth(result):
    assert len(result['causation']['cases']) == 32
    for row in result['causation']['cases']:
        assert row['results'] == [all(row['bits'])] * 2
    assert len(result['causation']['contrasts']) == 6
    assert all(row == [False, False] for row in result['causation']['contrasts'].values())
    assert result['causation']['specialization_retains_variable_bindings']
    assert result['causation']['closed_template_roundtrips']


def test_universal_conditions_check_each_selected_contract(result):
    for field in ('universal', 'source_universal'):
        data = result[field]
        assert len(data['cases']) == 64
        assert data['quantified_individual_positions'] == 5
        assert data['combinations_per_model'] == 32
        for row in data['cases']:
            s1, s2, f1, f2, p1, p2 = row['bits']
            assert row['results'] == [(not s1 or f1) and (not s2 or f2),
                (not s1 or not p1) and (not s2 or not p2), s1 or s2]
        counterexample = next(r for r in data['cases'] if r['bits'] == [True, True, True, False, False, True])
        assert counterexample['results'] == [False, False, True]


def test_universal_denial_does_not_assert_eligible_or_formed_contracts(result):
    for field in ('universal', 'source_universal'):
        data = result[field]
        empty = [r for r in data['cases'] if not any(r['bits'][:2])]
        assert all(r['results'] == [True, True, False] for r in empty)
        assert data['actual_contract_formation_not_required']
        assert data['real_world_scope_completeness_not_proven']


def test_unknown_relations_remain_unknown(result):
    assert result['generic']['unknown_aims_refused']
    assert result['source']['unknown_aims_refused']
    assert result['causation']['unknown_cause_and_truth_refused']
    assert result['universal']['unknown_scope_and_norms_refused']
    assert result['source_universal']['unknown_scope_and_norms_refused']


def test_historical_statements_and_partial_status_are_preserved(result):
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-parameterized-goals.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 12
    assert child['statements'] == parent['statements'] and len(child['statements']) == 15
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert result['roundtrips'] and not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
