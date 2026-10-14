from itertools import product
import json

import pytest

from noema.constructed import parse
from scripts.compose_policy_recognition import ROOT, PARENT, SOURCE, CORE, BASIS, build, basis
from scripts.check_policy_recognition import generic_values, source_values, attribution


@pytest.mark.parametrize('aware,one,two,current,first,second', list(product((False, True), repeat=6)))
def test_true_content_awareness_and_positive_judgment_are_distinct(aware, one, two, current, first, second):
    selected = tuple(p for p, flag in (('one', one), ('two', two)) if flag)
    judgment = bool(selected) and (not one or first) and (not two or second)
    assert generic_values(aware, selected, (current, first, second)) == [
        True, judgment, aware and judgment, aware and judgment and current, current]


@pytest.mark.parametrize('variant', ('wrong_person', 'wrong_context', 'wrong_awareness_target', 'wrong_candidate_target'))
def test_binding_to_same_person_description_and_context(variant):
    assert generic_values(variant=variant) == [True, variant == 'wrong_awareness_target', False, False, True]


@pytest.mark.parametrize('variant,message', [('unknown_awareness', 'Unknown awareness'), ('unknown_candidates', 'Unknown candidates')])
def test_unknown_attitudes_are_not_filled_with_false_or_empty(variant, message):
    with pytest.raises(ValueError, match=message): generic_values(variant=variant)


@pytest.mark.parametrize('aware,actual', list(product((False, True), repeat=2)))
@pytest.mark.parametrize('candidates', ((), ('safe',), ('bad',), ('safe', 'bad')))
def test_actual_manuscript_uses_same_policy_in_each_epistemic_candidate(aware, actual, candidates):
    judgment = candidates == ('safe',)
    assert source_values(aware=aware, candidates=candidates, actual_safe=actual) == [True]*4 + [
        judgment, aware and judgment, aware and judgment and actual, aware and judgment and actual, actual]


@pytest.mark.parametrize('variant', ('wrong_person', 'wrong_context'))
def test_source_attitude_is_about_ruler_at_actual_evaluation_context(variant):
    assert source_values(variant=variant) == [True]*4 + [False]*4 + [True]


def test_source_attitude_neither_requires_action_execution_nor_changes_with_current_grant():
    assert source_values(actual_grant=True) == [True]*9


def test_pure_fixture_cache_agrees_with_uncached_false_actual_truth():
    assert source_values(actual_safe=False, memoize=False) == source_values(actual_safe=False) == [True]*6 + [False]*3


@pytest.mark.parametrize('path', (SOURCE, CORE))
def test_author_attribution_is_separate_from_factive_attitude_and_its_truth(path):
    assert len(attribution(parse((ROOT / path).read_text(encoding='utf-8')))) == 2


def test_parent_declarations_and_unrelated_statements_remain_identical():
    assert all((ROOT / path).read_text(encoding='utf-8') == text for path, text in build().items())
    assert json.loads((ROOT / BASIS).read_text(encoding='utf-8')) == basis()
    parent, source = [parse((ROOT / path).read_text(encoding='utf-8')) for path in (PARENT, SOURCE)]
    assert source['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert source['statements'][:-1] == parent['statements'][:-1]
    assert source['statements'][-1] != parent['statements'][-1]
    assert len(source['statements']) == len(parent['statements']) == 17
