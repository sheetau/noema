import json

import pytest

from noema.grammar import parse
from scripts.check_successive_cohorts import REPORT, build_report
from scripts.compose_successive_cohorts import ROOT, PARENT


@pytest.fixture(scope='module')
def result(): return build_report()


def test_successor_is_relative_to_valid_periodization(result):
    assert result['periods']['models'] == 128
    assert result['periods']['independent_interval_oracle']
    assert result['periods']['changing_catalog_can_change_successor']
    for variant in ('intervening', 'overlap', 'gap_inside', 'outside_history', 'no_selected_later', 'cyclic', 'reverse'):
        assert result['cohorts']['contrasts'][variant] == [False]


def test_members_can_survive_into_the_next_period(result):
    for variant in ('baseline', 'disjoint_members', 'same_members'):
        assert result['cohorts']['contrasts'][variant] == [True]
    assert result['cohorts']['contrasts']['same_group'] == [False]
    assert result['cohorts']['biological_parenthood_not_assumed']


def test_membership_is_exactly_bound_to_population_and_presence(result):
    for variant in ('empty_next', 'missing_member', 'nonhuman_member', 'extra_member', 'population_changed'):
        assert result['cohorts']['contrasts'][variant] == [False]
    assert result['cohorts']['unknown_relations_refused']


def test_cohort_identity_does_not_assert_an_undertaking(result):
    for row in result['source']['cases']:
        assert row['results'] == [True, row['aimed'] and row['solemnity']]


def test_parties_and_same_undertaking_acts_belong_to_earlier_period(result):
    for variant in ('act_outside', 'party_outside', 'late_context', 'wrong_goal'):
        assert result['source']['contrasts'][variant] == [True, False]
    for variant in ('same_members', 'disjoint_members'):
        assert result['source']['contrasts'][variant] == [True, True]


def test_later_cohort_causal_goal_is_closed_and_not_executed(result):
    for flag in ('later_holder_and_period_fixed_in_goal', 'earlier_parties_are_causal_agents',
                 'unknown_achievement_not_evaluated', 'closed_roundtrips', 'standalone_agrees'):
        assert result['source'][flag]
    assert all(s['disquotations_removed'] > 0 for s in result['source']['specialization'])


def test_achieved_result_requires_same_later_cohort_and_causal_relation(result):
    assert len(result['source']['achieved_cases']) == 4
    for row in result['source']['achieved_cases']:
        assert row['result'] == (row['caused'] and row['later_unavailable'])


def test_parent_and_partial_status_are_preserved(result):
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-successive-cohorts.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 8
    assert child['statements'] == parent['statements'] and len(child['statements']) == 15
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert not result['alignment']['semantic_completion']
    assert result['source']['collective_representation_not_proven']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
