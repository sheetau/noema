from copy import deepcopy
import json
import pytest
from noema.constructed import parse,format_graph
from scripts.check_caused_choice import values,source_values,attribution,document,alignment,CONTRASTS,UNKNOWNS
from scripts.compose_caused_choice import ROOT,PARENT,SOURCE,CORE,BASIS,build,basis
from scripts.check_thinking_disposition import code_is


@pytest.mark.parametrize('table',range(16))
def test_all_boolean_response_equations_require_assessed_dependence_on_the_factor(table):
    # With F observed true, G observed true, and G=f(F,G), only G=F
    # has all off solutions G=false and all on solutions G=true.
    assert values(table)==[table==12]


@pytest.mark.parametrize('variant',CONTRASTS)
def test_invalid_observation_missing_assessment_or_empty_solution_set_is_not_causal_evidence(variant):
    assert values(variant=variant)==[False]


@pytest.mark.parametrize('variant',UNKNOWNS)
def test_unknown_data_remain_unknown(variant):
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant)


def test_source_assesses_counterfactual_capacity_using_the_same_actual_activity_catalogue():
    # The test interpretation intentionally provides an empty catalogue and zero
    # bound under offstart: using those instead of the fixed actual scope fails.
    assert source_values(indices=(0,1,2,5,6))==[True,True,True,True,False]


def test_missing_counterfactual_assessment_is_not_evidence_that_the_factor_caused_growth():
    assert source_values(variant='unassessed_off',indices=(0,5,6))==[False,False,False]


def test_same_growth_without_the_factor_rejects_causal_dependence():
    assert source_values(table=15,indices=(0,1,2))==[False,True,True]


def test_counterfactual_factor_name_cannot_override_the_actual_selected_development_content():
    assert source_values(variant='wrong_off_premise',indices=(0,5,6))==[False,True,False]


@pytest.mark.parametrize('variant',('wrong_observed_start','wrong_observed_end','wrong_observed_history','wrong_observed_order'))
def test_observed_time_course_must_equal_the_conditional_time_course(variant):
    assert source_values(variant=variant,indices=(0,))==[False]


@pytest.mark.parametrize('variant',('unknown_world_history','unknown_off_results'))
def test_unknown_counterfactual_histories_and_results_are_not_silently_supplied(variant):
    with pytest.raises(ValueError,match='Unknown'):source_values(variant=variant,indices=(0,))


def test_integrated_conditional_keeps_both_reading_identities_and_still_requires_remainder():
    calls=[]
    assert source_values(indices=(3,4),calls=calls)==[True,True]
    assert calls and all((p,s,e)==('person','end','after') for c,p,s,e in calls)
    assert any(code_is(c,'iahinner',1) for c,p,s,e in calls)
    assert any(code_is(c,'iahvocation',1) for c,p,s,e in calls)
    assert source_values(remaining=False,indices=(3,))==[False]


def test_false_development_does_not_assert_its_effect_or_require_a_causal_model():
    assert source_values(urge=False,assigned=False,variant='unknown_world_history',indices=(3,4))==[True,True]


def test_attribution_keeps_context_and_does_not_execute_the_partial_template():
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]


def test_template_rank_cannot_be_lowered():
    doc=deepcopy(document(CORE));d=next(d for d in doc['declarations'] if d['name']=='iakattribution')
    code=d['body']['arguments'][2];assert code['rank']==2;code['rank']=1
    with pytest.raises(ValueError):parse(format_graph(doc,'compact'))


def test_generic_uncached_baseline_history_and_artifacts():
    assert values(memoize=False)==values()
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert alignment()['remaining_consequent_unfilled'] and not alignment()['adds_new_text_coverage']
    assert all((ROOT/p).read_text(encoding='utf-8')==text for p,text in build().items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
