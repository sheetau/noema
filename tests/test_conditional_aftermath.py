from copy import deepcopy
from itertools import product
import json
import pytest
from noema.constructed import parse,format_graph
from scripts.check_conditional_aftermath import (values,source_values,attribution,document,alignment,
    CONTRASTS,UNKNOWNS)
from scripts.compose_conditional_aftermath import ROOT,PARENT,SOURCE,CORE,BASIS,build,basis
from scripts.check_thinking_disposition import code_is


@pytest.mark.parametrize('premises,results',list(product(range(4),repeat=2)))
def test_all_selected_cases_obey_condition_without_asserting_current_antecedent(premises,results):
    assert values(premises=premises,results=results)==[premises&~results==0,premises!=0,False]


def test_false_antecedents_allow_a_conditional_but_not_a_witness_or_executed_consequence():
    assert values(premises=0,variant='forbidden_result')==[True,False,False]


def test_one_true_antecedent_does_not_execute_the_other_cases_unknown_consequence():
    assert values(premises=1,results=1,variant='unknown_unused_result')==[True,True,False]


@pytest.mark.parametrize('variant',CONTRASTS)
def test_unrelated_people_readings_histories_or_invalid_temporal_scope_cannot_supply_a_result(variant):
    assert values(variant=variant,indices=(0,))==[False]


def test_equal_truth_values_do_not_make_distinct_readings_interchangeable():
    assert values(second=3,indices=(0,2))==[True,False]
    assert values(second=3,variant='wrong_reading',indices=(0,2))==[False,True]


def test_a_reading_that_works_per_case_cannot_be_chosen_anew_inside_each_case():
    assert values(second=3,variant='split_readings',indices=(0,2))==[False,False]


def test_consequence_receives_exact_chosen_reading_person_and_start_with_its_own_endpoint():
    calls=[]
    assert values(calls=calls,indices=(0,))==[True]
    assert calls and all(code_is(c,'jcfirstreading',1) and p=='person' for c,p,s,e in calls)
    assert {(s,e) for c,p,s,e in calls}=={('one','laterone'),('two','latertwo')}


@pytest.mark.parametrize('variant',UNKNOWNS)
def test_unknown_required_data_are_not_replaced_by_false_or_an_invented_result(variant):
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(0,))


@pytest.mark.parametrize('urge,assigned',list(product((False,True),repeat=2)))
def test_source_uses_the_actual_selected_development_and_checks_witnesses_separately(urge,assigned):
    assert source_values(urge=urge,assigned=assigned,result=False)==[not urge,not assigned,urge,assigned,False]


def test_source_preserves_reading_through_mapping_development_and_consequence():
    assert source_values(variant='vocation_only',indices=(0,1))==[False,True]
    calls=[]
    assert source_values(calls=calls)==[True,True,True,True,False]
    assert all((p,s,e)==('person','end','after') for c,p,s,e in calls)
    assert any(code_is(c,'iahinner',1) for c,p,s,e in calls)
    assert any(code_is(c,'iahvocation',1) for c,p,s,e in calls)


@pytest.mark.parametrize('variant',('empty_people','empty_cases','other_anchor','other_person','other_history'))
def test_source_does_not_repair_empty_scopes_or_mismatched_contexts(variant):
    assert source_values(variant=variant,indices=(0,1))==[False,False]


@pytest.mark.parametrize('variant',('unknown_source_cases','unknown_source_result'))
def test_source_propagates_unknown_inputs(variant):
    with pytest.raises(ValueError,match='Unknown'):source_values(variant=variant,indices=(0,))


def test_source_false_premise_does_not_need_an_evaluated_consequence():
    assert source_values(urge=False,assigned=False,variant='unknown_source_result')==[True,True,False,False,False]


def test_source_checks_later_result_only_in_the_case_where_development_occurs():
    assert source_values(variant='unknown_unused_result')==[True,True,True,True,False]


def test_attribution_does_not_execute_the_unfilled_template():
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]


def test_an_executed_rank_one_description_requires_rank_two_for_its_template():
    doc=deepcopy(document(CORE))
    d=next(d for d in doc['declarations'] if d['name']=='iaiattribution')
    code=d['body']['arguments'][2];assert code['rank']==2;code['rank']=1
    with pytest.raises(ValueError):parse(format_graph(doc,'compact'))


def test_uncached_evaluation_agrees_and_preserved_history_and_artifacts_reproduce():
    assert values(memoize=False)==values()
    assert source_values(memoize=False,indices=(0,))==source_values(indices=(0,))
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert alignment()['consequent_unfilled'] and not alignment()['adds_new_text_coverage']
    assert all((ROOT/p).read_text(encoding='utf-8')==text for p,text in build().items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
