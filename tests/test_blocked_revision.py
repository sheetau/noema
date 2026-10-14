import json

import pytest

from noema.grammar import parse
from scripts.check_blocked_revision import REPORT, build_report
from scripts.compose_blocked_revision import ROOT, PARENT


@pytest.fixture(scope='module')
def result(): return build_report()


def test_possible_success_is_not_success_guarantee(result):
    generic = result['generic']
    assert generic['models'] == 128 and generic['methods'] == 2
    assert generic['independent_set_oracle']
    assert generic['empty_results_do_not_prove_inability']
    assert result['source']['contrasts']['risky'] == [False] * 4


def test_two_goals_can_be_reached_by_different_methods(result):
    for case in result['source']['cases']:
        enabled, nonempty, gain, decrease, complete = case['bits']
        valid = not enabled or nonempty
        expected = [valid and not (enabled and nonempty and success) for success in (gain, decrease, decrease and complete)]
        assert case['results'] == expected + [expected[0] and expected[1]]
    assert result['source']['separate_methods_can_satisfy_separate_goals']


def test_partial_cleanup_is_possible_even_if_full_cleanup_is_not(result):
    case = next(c for c in result['source']['cases'] if c['bits'] == [True, True, True, True, False])
    assert case['results'] == [False, False, True, False]


def test_no_available_method_differs_from_missing_outcomes(result):
    for case in result['source']['cases']:
        enabled, nonempty, *_ = case['bits']
        if not enabled: assert case['results'] == [True] * 4
        elif not nonempty: assert case['results'] == [False] * 4
    assert result['source']['unknown_relations_refused']


def test_actor_start_holder_and_assessment_are_bound(result):
    c = result['source']['contrasts']
    assert c['other_actor'] == c['other_start'] == [False] * 4
    assert c['other_holder'] == c['assessment_changed'] == [True] * 4
    assert c['no_prior_errors'] == [False, True, True, False]


def test_causal_attribution_and_actual_blockage_are_both_needed(result):
    for case in result['causation']['cases']:
        assert case['results'] == [True] + [case['caused'] and case['blocked']] * 2
    for row in result['causation']['contrasts'].values(): assert row == [True, False, False]
    assert result['causation']['dynamic_and_specialized_agree']


def test_unknown_causal_result_can_be_stated_as_a_goal(result):
    assert result['causation']['closed_goal_roundtrips']
    assert result['causation']['unknown_goal_not_evaluated']
    assert all(s['disquotations_removed'] > 0 for s in result['causation']['specialization'])


def test_parent_preserved_and_source_completion_not_inferred(result):
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-blocked-revision.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 6
    assert child['statements'] == parent['statements'] and len(child['statements']) == 15
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
