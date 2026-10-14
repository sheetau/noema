import json

import pytest

from noema.grammar import parse
from scripts.check_necessary_futures import REPORT, build_report
from scripts.compose_necessary_futures import ROOT, PARENT, MODAL_PARENT


@pytest.fixture(scope='module')
def result(): return build_report()


def test_conditional_necessity_separates_applicability_and_current_truth(result):
    assert len(result['generic']['cases']) == 128
    for row in result['generic']['cases']:
        left, right, ca, cb, a, b, current = row['bits']
        applies = left and ca or right and cb
        condition = (left or right) and (not (left and ca) or a) and (not (right and cb) or b)
        assert row['results'] == [condition, applies, condition and applies]
    assert result['generic']['current_truth_not_required']
    assert result['generic']['applicability_does_not_evaluate_consequent']


def test_each_candidate_can_have_a_different_future_witness(result):
    assert result['generic']['future_contrasts']['different_witnesses'] == [True] * 6
    assert result['generic']['each_branch_can_have_its_own_witness']
    assert result['generic']['future_contrasts']['missing_branch'] == [False, True, False] * 2


def test_eventual_outcome_does_not_imply_persistent_outcome(result):
    assert result['generic']['future_contrasts']['mixed_branch'] == [True, True, True, False, True, False]
    assert result['source']['contrasts']['mixed_branch'] == [True, False, True]


def test_source_requires_all_applicable_candidates_not_one_success(result):
    assert len(result['source']['cases']) == 64
    for row in result['source']['cases']:
        left, right, ca, cb, a, b = row['bits']
        applies = left and ca or right and cb
        condition = (left or right) and (not (left and ca) or a) and (not (right and cb) or b)
        assert row['results'] == [condition and applies] * 2 + [condition]


def test_empty_candidates_unknown_data_and_vacuous_condition_are_distinct(result):
    assert result['source']['contrasts']['empty_candidates'] == [False] * 3
    assert result['source']['contrasts']['no_applicable'] == [False, False, True]
    assert result['source']['unknown_relations_refused']


def test_future_context_branch_and_period_stay_bound(result):
    for name in ('wrong_context', 'wrong_branch', 'wrong_epoch', 'not_future', 'only_current', 'missing_branch'):
        assert result['source']['contrasts'][name] == [False] * 3
    assert result['source']['actual_inability_does_not_substitute_future_inability']


def test_modal_causal_goals_can_be_purposes_without_achievement(result):
    assert set(result['purposes']) == {'hzdh', 'hzdi', 'hzdj'}
    for purpose in result['purposes'].values():
        assert purpose['unknown_modality_and_achievement_not_executed']
        assert purpose['closed_roundtrips'] and purpose['standalone_agrees']
        assert all(s['disquotations_removed'] > 0 for s in purpose['specialization'])


def test_scientific_definition_is_reused_without_changing_either_parent(result):
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-necessary-futures.noema').read_text(encoding='utf-8'))
    scientific = parse((ROOT / MODAL_PARENT).read_text(encoding='utf-8'))
    assert next(d for d in child['declarations'] if d['name'] == 's5k') == next(d for d in scientific['declarations'] if d['name'] == 's5k')
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 9
    assert child['statements'] == parent['statements'] and len(child['statements']) == 15
    assert result['reused_definitions'] == ['s5k'] and result['new_definitions'] == 8
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
