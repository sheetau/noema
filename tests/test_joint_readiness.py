from itertools import product
import pytest
from scripts.check_joint_readiness import values,full_domain_refused
from scripts.compose_joint_readiness import ROOT,build

@pytest.mark.parametrize('bits',list(product((False,True),repeat=4)))
def test_common_goal_and_each_members_fulfillment_share_one_plan(bits):
    a,p,q,g=bits;ready=a and p and q
    assert values(bits)==[True,ready,ready and g,ready,ready and g,True,ready]

@pytest.mark.parametrize('variant,expected',[
    ('separate_plans',[True,False,False,False,False,True,True]),
    ('good_and_bad_plans',[True,True,True,False,False,True,True]),
    ('empty_other_plan',[True,True,True,False,False,True,True]),
    ('goal_elsewhere',[True,True,False,True,False,True,True]),
    ('goal_not_all_plans',[True,True,True,True,True,True,True]),
    ('one_bad_realization',[True,False,False,False,False,True,False]),
    ('incoherent_other_plan',[True,True,True,False,False,True,True])])
def test_distributive_ability_common_readiness_and_all_plan_compliance_differ(variant,expected):
    assert values(variant=variant)==expected

@pytest.mark.parametrize('variant',('empty_selected','outside_outcome','wrong_planner','wrong_group','wrong_anchor','wrong_norm_source','wrong_norm_person','unlisted_requirement'))
def test_joint_plans_keep_the_same_scope_assessment_and_norms(variant):
    assert values(variant=variant)[:5]==[True,False,False,False,False]

@pytest.mark.parametrize('variant',('missing_member','extra_member','duplicate_member','empty_group','bad_indicator'))
def test_size_does_not_count_duplicates_or_an_incomplete_member_list(variant):
    assert values(variant=variant,indices=(0,1,2,3,4,5))==[False]*5+[True]

@pytest.mark.parametrize('threshold,expected',[(0,True),(1,True),(2,False),(3,False)])
def test_numerous_is_a_supplied_criterion_not_a_fixed_vocabulary_count(threshold,expected):
    assert values(threshold=threshold,indices=(0,2,3,4))==[expected,True,True,expected]

@pytest.mark.parametrize('variant',('unknown_availability','unknown_requirements','unknown_execution'))
def test_a_quoted_joint_condition_does_not_evaluate_unknown_inputs(variant):
    assert values(variant=variant,restricted=False,indices=(5,))==[True]
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(1,))

def test_full_requirement_description_domain_is_not_narrowed():
    assert full_domain_refused()

def test_cached_and_uncached_member_counts_and_joint_compliance_agree():
    assert values(memoize=False,indices=(0,1,5))==[True,True,True]

def test_saved_documents_reproduce():
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
