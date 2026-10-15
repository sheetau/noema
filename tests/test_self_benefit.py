from copy import deepcopy
from itertools import product
import json
import pytest
from noema.constructed import parse,format_graph
from scripts.check_self_benefit import values,source_values,attribution,document,alignment
from scripts.compose_self_benefit import ROOT,PARENT,SOURCE,CORE,BASIS,REVIEW,build,basis,reading_review
from scripts.check_thinking_disposition import code_is


@pytest.mark.parametrize('off,on',list(product(range(4),repeat=2)))
def test_guaranteed_goals_must_be_preserved_and_strictly_extended(off,on):
    assert values(off,on)==[True,off&~on==0 and off!=on]


@pytest.mark.parametrize('variant',('empty_goals','duplicate_goals','omitted_goal','empty_on','empty_off','unreviewed_off','wrong_realization'))
def test_invalid_scopes_or_unassessed_or_mismatched_outcomes_do_not_establish_benefit(variant):
    assert values(variant=variant)==[False,False]


def test_one_favorable_possible_result_does_not_guarantee_the_added_goal():
    assert values(variant='mixed_on')==[True,False]


@pytest.mark.parametrize('variant',('unknown_outcomes','unknown_goals','unknown_classification'))
def test_unknown_required_inputs_stay_unknown(variant):
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant)


def test_appraisal_can_hold_while_actual_benefit_fails():
    assert source_values()==[True,False]
    assert source_values(variant='actual_benefit')==[True,True]


def test_all_identity_fields_and_goal_scope_anchor_are_kept_through_judgment_candidates():
    calls=[]
    assert source_values(indices=(0,),calls=calls)==[True]
    goals=[row for row in calls if row[0]=='goals']
    assert goals and all(row[1:]==('government','political') for row in goals)
    views=[row for row in calls if row[0]=='view']
    assert views and all(row[1:4]==('government','government','government') and row[-2]=='political' for row in views)
    assert all(code_is(row[4],'jpnew') and code_is(row[5],'iatbenefit',1) for row in views)
    outcomes=[row for row in calls if row[0]=='outcome']
    assert outcomes and all(row[1]=='government' and code_is(row[2],'jpnew') and row[-2]=='outside' for row in outcomes)


@pytest.mark.parametrize('variant',('other_beneficiary','other_policy','empty_views','unrecognized','empty_off',
    'no_benefit','goal_exchange','mixed_on','unreviewed_off'))
def test_judgment_rejects_identity_swaps_empty_candidates_and_nonimprovements(variant):
    assert source_values(variant=variant,indices=(0,))==[False]


@pytest.mark.parametrize('variant',('unknown_views','unknown_outcomes','unknown_goal','unknown_review'))
def test_unknown_view_or_result_cannot_become_a_positive_judgment(variant):
    with pytest.raises(ValueError,match='Unknown'):source_values(variant=variant,indices=(0,))


def test_full_causal_conditional_requires_appraisal_but_not_actual_benefit():
    assert source_values(indices=(3,))==[True]
    assert source_values(variant='unrecognized',indices=(3,))==[False]


def test_attribution_keeps_rank_two_without_executing_its_content():
    for path in (CORE,SOURCE):assert attribution(path)==[True]
    doc=deepcopy(document(CORE));row=next(d for d in doc['declarations'] if d['name']=='iatattribution')
    assert row['body']['arguments'][2]['rank']==2
    row['body']['arguments'][2]['rank']=1
    with pytest.raises(ValueError):parse(format_graph(doc,'compact'))


def test_parent_preservation_artifact_reproducibility_and_explicit_limits():
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    assert json.loads((ROOT/REVIEW).read_text(encoding='utf-8'))==reading_review()
    assert not alignment()['adds_new_text_coverage'] and alignment()['dignity_content_unfilled']
    assert values(memoize=False)==values()
