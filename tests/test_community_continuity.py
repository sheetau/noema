from itertools import product
import pytest
from scripts.check_community_continuity import values
from scripts.compose_community_continuity import ROOT,build


@pytest.mark.parametrize('flags',list(product((False,True),repeat=4)))
def test_each_members_activity_and_holding_are_the_actual_common_protection_target(flags):
    assert values(flags)==[all(flags),all(flags),True,all(flags),flags[0]]


@pytest.mark.parametrize('variant',('late_scope_removal','late_activity_removal','late_item_removal','new_owner','wrong_scene_method'))
def test_loss_cannot_be_hidden_by_changing_the_scope_person_or_evaluation_time(variant):
    assert values(variant=variant)==[False,False,True,False,variant!='wrong_scene_method']


@pytest.mark.parametrize('variant',('wrong_community','empty_community','empty_person_activities','not_held_at_anchor','not_capable_at_anchor'))
def test_the_same_nonempty_community_and_valid_baseline_are_required(variant):
    assert values(variant=variant)==[False,False,False,False,True]


@pytest.mark.parametrize('variant',('wrong_activity_method','missing_assessment','multiple_task_outcomes','outside_taskoutcomes','wrong_goal_subject'))
def test_capability_uses_the_actual_person_task_and_nonempty_consistent_outcomes(variant):
    assert values(variant=variant)==[False]*5


def test_nonowners_are_included_and_each_person_can_use_a_different_method():
    assert values(variant='no_possessions')==[True]*5


@pytest.mark.parametrize('variant',('unknown_scope','unknown_holding','unknown_method','unknown_task'))
def test_quoting_a_profile_does_not_fill_unknown_facts(variant):
    assert values(variant=variant,indices=(6,))==[True]
    with pytest.raises(ValueError,match='Unknown'): values(variant=variant,indices=(8,))


def test_uncached_capability_is_reproducible():
    assert values(indices=(9,),memoize=False)==[True]


def test_documents_reproduce():
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
