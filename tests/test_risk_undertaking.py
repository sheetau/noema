from copy import deepcopy
from itertools import product
import json

import pytest

from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from scripts.check_risk_undertaking import (values,expected,source_values,attribution,document,model,
    DOMAIN,SCENES,CONTRASTS,NORM_CONTRASTS,alignment)
from scripts.compose_risk_undertaking import ROOT,PARENT,LIBRARY,EXAMPLE,SOURCE,CORE,BASIS,build,basis


@pytest.mark.parametrize('flags',list(product((False,True),repeat=8)))
def test_risk_belief_beginning_purpose_and_norms_remain_independent(flags):
    assert values(flags)==expected(flags)


@pytest.mark.parametrize('actual,achieved',list(product((False,True),repeat=2)))
def test_recognized_risk_need_not_be_actual_and_undertaking_need_not_succeed(actual,achieved):
    flags=(True,)*7+(False,)
    assert values(flags,actual_possible=actual,achieved=achieved)==expected(flags,actual,achieved)


@pytest.mark.parametrize('variant',CONTRASTS)
def test_same_person_activity_description_view_and_outcome_must_support_the_attempt(variant):
    result=values(variant=variant)
    assert result[2] is False and result[3:5]==[True,False]


@pytest.mark.parametrize('variant',NORM_CONTRASTS)
def test_normative_facts_cannot_be_borrowed_from_another_target(variant):
    result=values(variant=variant)
    assert result[1:5]==[True,True,False,True]


def test_goal_description_is_not_executed_to_decide_risk_or_permission():
    assert values(variant='unknown_goal',indices=(0,1,2,3,4,6))==[False,True,True,True,False,True]
    with pytest.raises(ValueError,match='Unknown goal'):values(variant='unknown_goal',indices=(5,))


def test_empty_choices_do_not_prove_an_attempt_or_inability():
    assert values(variant='empty_candidates')==[False,True,True,True,True,False,True]
    assert source_values(variant='empty_candidates')==[True,True,True,True]
    assert source_values(variant='empty_population',allowed=True,indices=(0,))==[True]


def test_another_selected_permitted_activity_prevents_universal_denial():
    doc=deepcopy(document(EXAMPLE));doc['statements']=doc['statements'][4:5]
    primitives=model((True,)*6+(False,False))
    primitives['jracandidates']=lambda p,a,c:(p,c)==('person','anchor') and a in ('trial','secondtrial')
    primitives['jraallowed']=lambda s,p,r,a,d,sign,c:(s,p,r,a,sign,c)==('standard','person','role','secondtrial',True,'anchor') and json.loads(d.syntax)==dict(kind='function_ref',symbol='jragoal')
    result=evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=primitives)
    assert result==[dict(kind='ask',value=False)]


@pytest.mark.parametrize('allowed,forbidden,success,begins',list(product((False,True),repeat=4)))
def test_source_uses_the_same_utterance_without_equating_denial_failure_and_inactivity(allowed,forbidden,success,begins):
    assert source_values(allowed=allowed,forbidden=forbidden,success=success,begins=begins)==[
        not (allowed and not forbidden),success,begins,True]


@pytest.mark.parametrize('variant',('wrong_speaker','wrong_context','wrong_anchor','extra_hearer','missing_hearer'))
def test_reference_mismatch_is_not_evidence_for_denial(variant):
    assert source_values(variant=variant,indices=(0,3))==[False,True]


@pytest.mark.parametrize('variant,index',(('unknown_norm',0),('unknown_goal',1),('unknown_prospects',2),('unknown_speaker',0)))
def test_unknown_inputs_remain_quotable_but_relevant_queries_refuse_them(variant,index):
    assert source_values(variant=variant,indices=(3,))==[True]
    with pytest.raises(ValueError,match='Unknown'):source_values(variant=variant,indices=(index,))


@pytest.mark.parametrize('allowed,qualified',list(product((False,True),repeat=2)))
def test_actual_previous_qualification_and_new_denial_are_combined(allowed,qualified):
    assert source_values(allowed=allowed,qualified=qualified,combined=True,indices=(0,3))==[qualified and not allowed,True]


@pytest.mark.parametrize('path',(SOURCE,CORE))
def test_source_attribution_keeps_risk_norms_and_actions_unevaluated(path):
    assert attribution(path)==[True]
    for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]


def test_source_retains_all_previous_statements_and_records_only_a_candidate_reading():
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements']
    assert alignment()['political_classification_open'] and not alignment()['semantic_completion']
    assert [s['text'] for s in alignment()['segments']]==['nicht wagen darf']


def test_lower_description_rank_cannot_hide_the_source_utterance_reference():
    doc=deepcopy(document(CORE))
    node=next(d for d in doc['declarations'] if d['name']=='iaaundertake')['body']['body']['arguments'][2]
    assert node['rank']==2
    node['rank']=1
    with pytest.raises(ValueError):parse(format_graph(doc,'compact'))


def test_uncached_evaluation_and_reproduced_artifacts_agree():
    assert values(memoize=False)==values()
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
