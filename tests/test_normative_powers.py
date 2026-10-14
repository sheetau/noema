import json

import pytest

from noema.grammar import parse
from scripts.check_normative_powers import REPORT, build_report
from scripts.compose_normative_powers import ROOT, PARENT


@pytest.fixture(scope='module')
def result(): return build_report()


def test_specific_norm_change_requires_both_endpoints_control_and_recognition(result):
    assert len(result['generic']['cases']) == 32
    for row in result['generic']['cases']:
        changed = row['prior'] != row['status'] and row['subsequent'] == row['status']
        power = changed and row['controlled'] and row['recognized']
        assert row['results'] == [changed, power, power, False]


def test_repealing_a_requirement_is_not_requiring_negative_content(result):
    assert {(r['polarity'], r['status']) for r in result['generic']['polarity_cases']} == {(a, b) for a in (False, True) for b in (False, True)}
    for row in result['generic']['polarity_cases']: assert row['results'] == [True, True, True, False]


def test_power_and_actual_exercise_are_independent(result):
    assert len(result['generic']['actual_cases']) == 8
    for row in result['generic']['actual_cases']:
        assert row['results'] == [True, row['recognized'], row['recognized'], row['recognized'] and row['performed'] and row['realized']]
    assert result['generic']['unknown_actuality_does_not_block_power']


def test_distinct_records_cannot_supply_a_single_recognized_change(result):
    contrasts = result['generic']['contrasts']
    assert len(contrasts) == 18
    for name in ('wrong_source', 'wrong_person', 'wrong_role', 'wrong_bindings', 'wrong_polarity', 'target_alias', 'bad_target_shape'):
        assert contrasts[name] == [False] * 4
    for name in ('wrong_actor', 'wrong_capacity', 'wrong_framework', 'exercise_alias', 'wrong_owner', 'bad_exercise_shape', 'split_result'):
        assert contrasts[name] == [True, False, False, False]
    for name in ('split_execution', 'split_realized'): assert contrasts[name] == [True, True, True, False]


def test_another_valid_result_can_witness_power_but_not_the_specified_actual_transition(result):
    for name in ('same_state', 'alternative'):
        assert result['generic']['contrasts'][name] == [False, False, True, False]


def test_permission_requirement_power_and_permission_power_are_separate(result):
    assert len(result['source']['cases']) == 32
    for row in result['source']['cases']:
        power = row['controlled'] and row['recognized']
        assert row['results'] == [power, power and row['permission_effect'], power and row['permission'] and not row['forbidden']]
    assert result['source']['permission_independent_of_power']
    assert result['source']['requirement_and_permission_effects_distinct']


def test_policy_truth_is_not_evaluated_and_unknown_norms_are_not_false(result):
    assert result['generic']['policy_truth_not_executed'] and result['generic']['unknown_relations_refused']
    assert result['generic']['standalone_agrees'] and result['source']['standalone_agrees']


def test_the_same_unresolved_power_can_be_questioned_and_denied(result):
    assert result['quoted'] == {'shared_negative_base': True, 'unknown_power_not_evaluated': True, 'roundtrips': True}


def test_parent_and_interpretive_status_are_preserved(result):
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    doc = parse((ROOT / 'examples/v014/kant-normative-powers.noema').read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(doc['declarations']) == len(parent['declarations']) + 7
    assert doc['statements'] == parent['statements'] and len(doc['statements']) == 15
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert result['alignment']['segments'][0]['text'] == 'berechtigt sein'
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
