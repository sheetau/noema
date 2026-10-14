import json

import pytest

from noema.grammar import parse
from scripts.check_question_responses import REPORT, build_report
from scripts.compose_question_responses import ROOT, PARENT


@pytest.fixture(scope='module')
def result(): return build_report()


def test_negative_question_does_not_turn_denial_into_affirmation(result):
    assert len(result['signed']) == 4
    for row in result['signed']:
        assert row['results'] == [row['truth'] == row['sign'], False]


@pytest.mark.parametrize('section', ['generic', 'source'])
def test_attribution_order_and_response_are_independent_conditions(result, section):
    rows = result[section]['cases']
    assert len(rows) == 16
    for row in rows: assert row['results'] == [all(row['bits'])]
    for name in ('wrong_author', 'wrong_context', 'reversed_order', 'reversed_response', 'same_node'):
        assert result[section]['contrasts'][name] == [False]


@pytest.mark.parametrize('section', ['generic', 'source'])
def test_shared_closed_base_preserves_question_and_answer_polarities(result, section):
    assert result[section]['shared_base_constructed']
    for name in ('positive_question', 'positive_answer', 'answer_alias'):
        assert result[section]['contrasts'][name] == [False]
    assert result[section]['closed_roundtrips']
    assert result[section]['standalone_agrees']
    assert result[section]['generic_relation_does_not_enforce_content_identity']


def test_asking_and_answering_do_not_assert_truth_in_the_interpretation(result):
    for name in ('generic', 'source'):
        assert result[name]['underlying_truth_not_required']
        assert result[name]['unknown_response_refused']


def test_normative_permission_is_neither_actual_success_nor_unknown_false(result):
    assert len(result['normative']['cases']) == 8
    for row in result['normative']['cases']:
        permission = row['allowed'] and not row['forbidden'] and row['valid']
        assert row['results'] == [True, permission, not permission]
    assert result['normative']['actual_policy_not_executed']
    assert result['normative']['unknown_permission_refused']


def test_parent_and_interpretive_status_are_preserved(result):
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    doc = parse((ROOT / 'examples/v014/kant-question-responses.noema').read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(doc['declarations']) == len(parent['declarations']) + 8
    assert doc['statements'] == parent['statements'] and len(doc['statements']) == 15
    assert result['new_definitions'] == 6 and result['new_primitives'] == 2
    assert result['new_author_statements'] == 0
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
