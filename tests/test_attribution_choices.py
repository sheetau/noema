import json

import pytest

from noema.grammar import parse
from scripts.check_attribution_choices import REPORT, build_report
from scripts.compose_attribution_choices import ROOT, PARENT


@pytest.fixture(scope='module')
def result(): return build_report()


def test_some_all_and_selected_attributions_have_distinct_conditions(result):
    for section in ('generic', 'source'):
        assert len(result[section]['cases']) == 8
        for row in result[section]['cases']:
            first, second, joined = row['bits']
            assert row['results'] == [first or second, first and second, first, second, False, joined]


def test_outer_choice_is_not_attributing_an_inner_disjunction(result):
    for section in ('generic', 'source'):
        rows = result[section]['cases']
        inner_only = next(r for r in rows if r['bits'] == [False, False, True])
        first_only = next(r for r in rows if r['bits'] == [True, False, False])
        assert inner_only['results'] == [False, False, False, False, False, True]
        assert first_only['results'] == [True, False, True, False, False, False]


def test_source_node_author_and_context_cannot_be_combined(result):
    for section in ('generic', 'source'):
        for name in ('other_node', 'other_author', 'other_context'):
            assert result[section]['contrasts'][name] == [False] * 6


def test_empty_choices_do_not_succeed_and_duplicates_do_not_vote(result):
    for section in ('generic', 'source'):
        contrasts = result[section]['contrasts']
        assert contrasts['empty'] == [False] * 6
        assert contrasts['duplicate'] == contrasts['reordered'] == [True, False, True, False, False, False]


def test_known_claim_of_an_alias_does_not_make_it_a_declared_candidate(result):
    for section in ('generic', 'source'):
        assert result[section]['claimed_nonmember_not_selected']
        assert all(row['results'][4] is False for row in result[section]['cases'])
        assert result[section]['no_automatic_reading_selection']
        assert result[section]['candidates_not_claimed_exhaustive']


def test_unknown_attribution_is_not_false_and_full_policy_contents_stay_quoted(result):
    for section in ('generic', 'source'):
        assert result[section]['unknown_attribution_refused']
        assert result[section]['underlying_contents_not_executed']


def test_partial_source_status_and_prior_author_claims_remain_unchanged(result):
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-attribution-choices.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 6
    assert child['statements'] == parent['statements'] and len(child['statements']) == 15
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
