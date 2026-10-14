import json

import pytest

from noema.grammar import parse
from scripts.check_epistemic_revision import REPORT, build_report
from scripts.compose_epistemic_revision import ROOT, PARENT


@pytest.fixture(scope='module')
def result(): return build_report()


@pytest.mark.parametrize('section', ['generic', 'source'])
def test_information_support_and_error_removal_are_independent(result, section):
    assert len(result[section]['cases']) == 32
    for row in result[section]['cases']:
        removed = row['keep'] and row['old_error'] and not row['new_error']
        want = [row['keep'], row['keep'] and row['add'] and row['warrant'], removed, removed]
        assert row['results'] == (want[1:] if section == 'source' else want)


def test_aliases_and_tautologies_do_not_inflate_information_or_error_removal(result):
    for name in ('true_alias', 'false_alias', 'tautology_added'):
        assert result['generic']['contrasts'][name] == [True, False, False, False]


def test_partial_cleanup_differs_from_complete_cleanup_and_new_false_content(result):
    assert result['generic']['contrasts']['partial_cleanup'] == [True, False, True, False]
    assert result['generic']['contrasts']['new_error_content'] == [True, False, False, False]


def test_discarding_correct_information_is_not_an_improvement(result):
    for name in ('discard_all', 'support_lost', 'other_holder'):
        assert result['generic']['contrasts'][name] == [False] * 4
    assert result['generic']['contrasts']['support_acquired'] == [True, True, False, False]


def test_preservation_compares_information_rather_than_retained_item_names(result):
    assert result['generic']['contrasts']['stronger_replacement'] == [True] * 4
    assert result['generic']['contrasts']['weaker_replacement'] == [False] * 4


def test_scope_and_assessment_limits_are_explicit(result):
    for name in ('empty_comparisons', 'missing_assessment', 'same_stage'):
        assert result['generic']['contrasts'][name] == [False] * 4
    assert result['generic']['contrasts']['empty_scope'] == [True, False, False, False]
    assert result['generic']['contrasts']['single_actual'] == [True, False, True, True]
    assert result['generic']['contrasts']['scope_excludes_error'] == [True] * 4
    assert result['generic']['contrasts']['stage_truth_changed'] == [True] * 4


def test_goals_can_be_stated_without_evaluating_unknown_epistemic_states(result):
    assert result['goals'] == {'constructors': ['hzc5', 'hzc6', 'hzc7'], 'unknown_goal_not_evaluated': True, 'roundtrips': True}
    for section in ('generic', 'source'):
        assert result[section]['unknown_relations_refused']
        assert result[section]['standalone_agrees']
        assert result[section]['fixed_holder_scope_and_assessment']


def test_parent_and_partial_status_are_preserved(result):
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    doc = parse((ROOT / 'examples/v014/kant-epistemic-revision.noema').read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(doc['declarations']) == len(parent['declarations']) + 9
    assert doc['statements'] == parent['statements'] and len(doc['statements']) == 15
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert [s['text'] for s in result['alignment']['segments']] == ['Erkenntnisse zu erweitern', 'von Irrthümern zu reinigen']
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
