from copy import deepcopy
from fractions import Fraction
from itertools import product
import json
import pytest
from noema.constructed import parse,format_graph
from scripts.check_gradual_choice import values,source_values,attribution,document,alignment,CONTRASTS,UNKNOWNS
from scripts.compose_gradual_choice import ROOT,PARENT,SOURCE,CORE,BASIS,build,basis
from scripts.check_thinking_disposition import code_is


@pytest.mark.parametrize('counts',list(product(range(4),repeat=3)))
def test_three_point_profiles_keep_the_same_catalogue_and_bound(counts):
    expected=counts[0]<counts[1]<counts[2] and counts[1]-counts[0]<=1 and counts[2]-counts[1]<=1
    assert values(tuple((1<<n)-1 for n in counts),indices=(0,))==[expected]


@pytest.mark.parametrize('variant',CONTRASTS)
def test_no_omission_unknown_as_incapacity_scope_substitution_or_invalid_history(variant):
    assert values(variant=variant,indices=(0,))==[False]


@pytest.mark.parametrize('variant',UNKNOWNS)
def test_unknown_required_input_is_not_treated_as_an_absent_activity(variant):
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(0,))


@pytest.mark.parametrize('bound',(-1,0,Fraction(1,2)))
def test_invalid_or_too_small_step_limit_rejects_the_same_growth(bound):
    assert values(bound=bound,indices=(0,))==[False]


def test_equal_limit_reordered_catalogue_and_larger_limit():
    assert values(bound=1,indices=(0,))==[True]
    assert values(bound=2,variant='reordered',indices=(0,))==[True]
    assert values((0,3,7),bound=2,indices=(0,))==[True]
    assert values((0,3,7),bound=1,indices=(0,))==[False]


def test_count_growth_cannot_hide_a_lost_choice_by_replacing_it_with_two_others():
    assert values((1,3,7),indices=(0,))==[True]
    assert values((1,6,7),indices=(0,))==[False]


def test_a_plateau_is_allowed_but_a_single_jump_is_not():
    assert values((1,3,3,7),indices=(0,))==[True]
    assert values((1,1,1,7),bound=3,indices=(0,))==[False]


@pytest.mark.parametrize('profile,variant,expected',[
    ((1,1,1),'baseline',True),((0,0,0),'baseline',False),((1,1,1),'no_skip',False),((1,1,1),'mixed_results',False)])
def test_both_execution_and_refraining_need_their_own_successful_method(profile,variant,expected):
    assert values(profile,variant=variant,indices=(1,2,4))==[expected,True,False]


def test_a_missing_result_is_distinct_from_an_assessed_lack_of_choice():
    assert values((0,0,0),indices=(1,2))==[False,True]
    assert values((0,0,0),variant='unassessed_method',indices=(1,2))==[False,False]


def test_source_connects_actual_method_based_growth_without_asserting_execution():
    calls=[]
    assert source_values(calls=calls)==[True,True,True,False]
    assert calls and all((p,s,e)==('person','end','after') for c,p,s,e in calls)
    assert any(code_is(c,'iahinner',1) for c,p,s,e in calls)
    assert any(code_is(c,'iahvocation',1) for c,p,s,e in calls)


def test_source_rejects_abrupt_growth_and_keeps_the_unfilled_remainder_necessary():
    assert source_values(profile=(1,1,7))==[False,False,False,False]
    assert source_values(remaining=False)==[False,False,True,False]
    assert source_values(variant='vocation_only',indices=(0,1))==[False,True]


@pytest.mark.parametrize('variant',('other_performer','nonhuman'))
def test_someone_elses_action_or_a_nonhuman_does_not_supply_the_source_capacity(variant):
    assert source_values(variant=variant,indices=(2,3))==[False,False]


def test_false_development_does_not_assert_growth_or_evaluate_the_remainder():
    assert source_values(profile=(1,1,7),urge=False,assigned=False,variant='unknown_remaining')==[True,True,False,False]
    with pytest.raises(ValueError,match='Unknown'):source_values(variant='unknown_remaining',indices=(0,))


def test_attribution_preserves_context_and_does_not_execute_the_candidate():
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]


def test_template_rank_cannot_be_lowered():
    doc=deepcopy(document(CORE));d=next(d for d in doc['declarations'] if d['name']=='iajattribution')
    code=d['body']['arguments'][2];assert code['rank']==2;code['rank']=1
    with pytest.raises(ValueError):parse(format_graph(doc,'compact'))


def test_uncached_baselines_history_and_artifacts():
    assert values(memoize=False)==values()
    assert source_values(memoize=False,indices=(2,))==[True]
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert alignment()['remaining_consequent_unfilled'] and not alignment()['adds_new_text_coverage']
    assert all((ROOT/p).read_text(encoding='utf-8')==text for p,text in build().items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
