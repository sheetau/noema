from copy import deepcopy
from itertools import product
import json
import pytest
from noema.constructed import parse,format_graph
from scripts.check_assessed_barriers import (values,attribution,document,independent,alignment,CONTRASTS,UNKNOWNS)
from scripts.compose_assessed_barriers import ROOT,PARENT,SOURCE,CORE,BASIS,build,basis


@pytest.mark.parametrize('table',range(16))
def test_intervention_solutions_match_independent_fixed_point_enumeration(table):
    result=values(table=table)
    assert result[2:5]==[independent(table)]*3


@pytest.mark.parametrize('flags',list(product((False,True),repeat=3)))
def test_appearance_counterfactual_success_and_actual_factor_are_independent(flags):
    appearance,success,observed=flags
    result=values(appearance=appearance,off_success=success,observed_on=observed)
    assert result[0]==appearance
    assert result[2:4]==[success and observed]*2
    assert result[4]==all(flags)


@pytest.mark.parametrize('variant',CONTRASTS)
def test_regime_scope_goal_observation_and_assessment_cannot_be_substituted(variant):
    assert values(variant=variant)[4] is False


@pytest.mark.parametrize('variant',('unassessed_on','empty_evaluation','invalid_evaluation'))
def test_unassessed_failure_is_not_verified_inability(variant):
    result=values(variant=variant)
    assert result[0:2]==[True,True]
    assert result[2:7]==[False]*5


def test_one_valid_off_method_is_enough_even_if_another_off_method_is_unassessed():
    assert values(variant='unassessed_off')==[True]*8


def test_known_empty_method_scope_is_not_unknown_method_scope():
    assert values(variant='no_methods_on')==[True]*8
    with pytest.raises(ValueError,match='Unknown'):values(variant='unknown_methods',indices=(4,))


def test_matching_factor_truth_is_not_enough_when_the_permission_regime_changes():
    result=values(variant='changed_off_regime')
    assert result==[True,False,True,False,False,True,True,True]


def test_unreachable_under_both_settings_is_not_a_barrier_caused_by_the_factor():
    result=values(off_success=False)
    assert result[2:5]==[False]*3
    assert result[5:7]==[True,True]


def test_multiple_on_solutions_include_the_successful_escape():
    result=values(table=10) # opportunity = itself: both values remain solutions.
    assert result[2:5]==[False]*3
    assert result[6] is True # Current failure alone does not exclude an escape.


@pytest.mark.parametrize('variant',UNKNOWNS)
def test_unknowns_can_be_quoted_but_cannot_be_used_as_known_barriers(variant):
    assert values(variant=variant,indices=(7,))==[True]
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(4,))


@pytest.mark.parametrize('path',(SOURCE,CORE))
def test_attribution_does_not_execute_the_claim_or_lose_its_source(path):
    assert attribution(path)==[True]
    for variant in ('node','author','scope','anchor'):assert attribution(path,variant)==[False]


def test_reference_rank_cannot_be_erased():
    doc=deepcopy(document(CORE));d=next(d for d in doc['declarations'] if d['name']=='iadattribution')
    code=d['body']['arguments'][2];assert code['rank']==3;code['rank']=2
    with pytest.raises(ValueError):parse(format_graph(doc,'compact'))


def test_history_and_interpretive_status_are_retained():
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert alignment()['semantic_completion'] is False
    assert alignment()['causal_model_relative'] is True


def test_artifacts_reproduce_and_caching_does_not_change_the_result():
    assert values(memoize=False,budget=20_000_000)==values()
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
