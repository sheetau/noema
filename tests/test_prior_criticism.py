from itertools import product

import pytest

from scripts.check_prior_criticism import values, joint_action, attribution
from scripts.compose_prior_criticism import ROOT, PARENT, SOURCE, CORE, build
from noema.constructed import parse


@pytest.mark.parametrize('past,permit,old_now,old_future,adverse,aware', list(product((False, True), repeat=6)))
def test_prior_adoption_permission_and_safety_keep_their_distinct_conditions(past, permit, old_now, old_future, adverse, aware):
    critical = past and permit
    safety = critical and old_future and not adverse
    assert values(past, permit, old_now, old_future, adverse, aware) == [True, critical, critical and old_now, safety, safety and aware]


@pytest.mark.parametrize('variant', ('future_only', 'other_history', 'missing_anchor', 'cycle', 'reversed_time',
    'other_law', 'other_adopter', 'wrong_law_role', 'wrong_law_polarity', 'wrong_condition', 'wrong_goal',
    'wrong_domain', 'wrong_target', 'wrong_public_role'))
def test_unrelated_adoptions_or_permissions_cannot_satisfy_the_source_binding(variant):
    assert values(variant=variant) == [True, False, False, False, False]


@pytest.mark.parametrize('past,current', list(product((False, True), repeat=2)))
def test_already_adopted_does_not_require_current_adoption(past, current):
    assert values(past=past, current_adoption=current) == [True, past, past, past, past]


@pytest.mark.parametrize('variant,expected', [
    ('old_policy_prospects', [True, True, True, False, False]),
    ('old_safety_awareness', [True, True, True, True, False]),
])
def test_risk_and_awareness_must_address_the_new_combined_content(variant, expected):
    assert values(variant=variant) == expected


def test_empty_selection_does_not_assert_a_previously_adopted_law_exists():
    assert values(past=False, permission=False, selected=False) == [True] * 5


@pytest.mark.parametrize('variant,message', [
    ('unknown_adoption', 'Unknown prescription adoption'),
    ('unknown_history', 'Unknown temporal order'),
    ('unknown_selector', 'Unknown assessment selector'),
])
def test_unknown_reference_or_selection_is_not_filled_in(variant, message):
    with pytest.raises(ValueError, match=message):
        values(variant=variant, indices=(1,))


@pytest.mark.parametrize('comparison,criticism', list(product((False, True), repeat=2)))
def test_comparison_and_criticism_must_both_be_present_in_the_joint_action(comparison, criticism):
    assert joint_action(comparison, criticism) == (comparison and criticism)


@pytest.mark.parametrize('variant', ('other_person', 'other_act', 'other_context'))
def test_joint_action_does_not_combine_different_people_acts_or_contexts(variant):
    assert joint_action(variant=variant) is False


def test_source_target_construction_does_not_execute_its_criticism():
    # All actual judgment, criterion and public-presentation primitives raise in this fixture.
    assert values(indices=(0, 1)) == [True, True]


def test_permission_for_both_separate_actions_does_not_grant_the_joint_action():
    assert values(variant='separate_permissions', parts=True) == [True, False, False, False, False, True, True]


def test_pure_cache_and_uncached_new_policy_evaluation_agree():
    assert values(indices=(0, 1, 2), memoize=False) == values(indices=(0, 1, 2)) == [True] * 3


def test_source_preserves_previous_definitions_and_prior_attributions():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    source = parse((ROOT / SOURCE).read_text(encoding='utf-8'))
    assert source['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert source['statements'][:-1] == parent['statements'][:-1]
    assert all((ROOT / path).read_text(encoding='utf-8') == text for path, text in build().items())
    for path in (SOURCE, CORE):
        assert attribution(parse((ROOT / path).read_text(encoding='utf-8'))) == [
            [dict(kind='assert', value=False)], [dict(kind='assert', value=True)]]
