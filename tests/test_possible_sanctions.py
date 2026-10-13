import json

import pytest

from noema.grammar import parse
from scripts.check_possible_sanctions import REPORT, build_report
from scripts.compose_possible_sanctions import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_possibility_permission_and_actuality_are_independent(result):
    rows = result['source']['cases']
    assert len(rows) == 64
    for row in rows:
        causal, executed, adverse, intended, response, permitted = row['states']
        assert row['results'] == [causal, executed and adverse and intended and response, permitted, False]
    assert result['source']['standalone_agrees']


def test_possible_causation_requires_occurrence_causal_relation_and_effect_in_one_outcome(result):
    rows = result['source']['causal_cases']
    assert len(rows) == 8
    assert all(row['result'] == all(row['states']) for row in rows)
    contrasts = result['source']['contrasts']
    for name in ('wrong_causal_activity', 'wrong_effect_subject', 'wrong_effect_description',
                 'split_causes_and_effect', 'cooccurrence_only'):
        assert contrasts[name] == [False, True, True, False]


def test_empty_candidates_and_unrelated_actual_sanctions_do_not_supply_possibility(result):
    rows = result['source']['contrasts']
    assert rows['empty_candidates'] == rows['wrong_evaluation_context'] == [False, False, True, False]
    assert rows['actual_only'] == [True, False, True, True]
    assert rows['mixed_candidates'] == [True, True, True, False]


def test_response_binds_actor_measure_target_offense_assessment_and_situation(result):
    rows = result['source']['contrasts']
    for name in ('wrong_authority', 'wrong_adverse_measure', 'wrong_adverse_person',
                 'wrong_intended_measure', 'wrong_intended_person', 'wrong_offense',
                 'wrong_assessment', 'split_response'):
        assert rows[name] == [True, False, True, False]
    assert rows['opposed_requirement'] == [True, True, False, False]


def test_assessment_truth_and_sanction_execution_are_not_needed_for_permission(result):
    assert result['source']['assessment_not_executed']
    assert result['source']['permission_without_execution_information']
    assert result['source']['unknown_adverse_effect_refused']
    desc = result['source']['sanction_description']
    assert desc['kind'] == 'call' and desc['symbol'] == 'hzat'
    assert desc['arguments'][2] == {'kind': 'quote', 'body': {'kind': 'function_ref', 'symbol': 'zk'}}
    assert result['causal_disquotation_cannot_be_quoted']


def test_extent_uses_an_explicit_criterion_and_valid_population(result):
    rows = result['extent']['cases']
    assert len(rows) == 60
    assert any(row['result'] and row['count'] < row['size'] for row in rows)
    assert all(not value for value in result['extent']['invalid'].values())
    assert result['extent']['criterion_is_explicit_not_a_fixed_universal_threshold']


def test_parent_author_claims_and_primitive_inventory_are_preserved(result):
    text, basis = source_composed(); doc = parse(text)
    parent = parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(doc['declarations']) - len(parent['declarations']) == 10
    assert doc['statements'] == parent['statements'] and len(doc['statements']) == 15
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert result['documents'][basis['document']]['primitive_count'] == 252


def test_partial_interpretation_does_not_certify_full_source_equivalence(result):
    assert len(result['alignment']['segments']) == 2
    assert all(row['status'] == 'partial' for row in result['alignment']['segments'])
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}


def test_reproducible_report_and_roundtrips(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert result['parent_preserved'] and result['roundtrips']
