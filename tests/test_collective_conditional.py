from copy import deepcopy
from itertools import product
import json
import pytest
from noema.constructed import parse,format_graph
from scripts.check_collective_conditional import values,source_values,attribution,document,alignment,CONTRASTS,UNKNOWNS,SOURCE_CONTRASTS
from scripts.compose_collective_conditional import ROOT,PARENT,SOURCE,CORE,BASIS,build,basis
from scripts.check_thinking_disposition import code_is


@pytest.mark.parametrize('first,second,result',list(product(range(4),repeat=3)))
def test_all_two_person_two_case_truth_and_consequence_combinations(first,second,result):
    masks=(first,second)
    want=all(mask!=3 or bool(result&(1<<i)) for i,mask in enumerate(masks))
    assert values(masks,result)==[want,3 in masks]


@pytest.mark.parametrize('variant',CONTRASTS)
def test_empty_or_invalid_scopes_histories_or_changed_result_identity_reject_conditional(variant):
    assert values(variant=variant)[0] is False


@pytest.mark.parametrize('variant',UNKNOWNS)
def test_unknown_required_inputs_do_not_become_false_premises(variant):
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant)


def test_false_joint_premises_need_no_result_but_still_need_valid_scopes():
    assert values((1,2),variant='unknown_result')==[True,False]
    assert values((1,2),variant='invalid_second')==[False,False]
    with pytest.raises(ValueError,match='Unknown'):values((1,2),variant='unknown_valid')


def test_generic_remainder_receives_the_same_reading_coalition_and_interval():
    calls=[]
    assert values((3,3),calls=calls)==[True,True]
    assert calls and all(code_is(r[0],'jgproperty',1) and r[1]==('person','other') and r[3]==r[2]+'end' for r in calls)
    assert {r[2] for r in calls}=={'first','second'}


def test_full_source_connects_both_readings_and_keeps_all_remainder_arguments():
    calls=[]
    assert source_values(indices=(0,1,2),calls=calls)==[True,True,True]
    rest=[r for r in calls if r[0]=='remaining']
    assert rest and all(r[2:]==('community',('person','other'),'end','end','after') for r in rest)
    assert any(code_is(r[1],'iahinner',1) for r in rest)
    assert any(code_is(r[1],'iahvocation',1) for r in rest)


@pytest.mark.parametrize('variant',SOURCE_CONTRASTS)
def test_source_rejects_missing_or_exchanged_scope_and_mismatched_causal_history(variant):
    assert source_values(variant=variant,indices=(0,))==[False]


@pytest.mark.parametrize('variant',('changed_contributors','changed_topics','changed_activities','changed_bound'))
def test_scope_changes_cannot_be_hidden_in_cases_with_false_joint_antecedents(variant):
    assert source_values(variant=variant,all_false=True,indices=(0,3))==[False,False]


def test_complete_catalogues_may_be_reordered_without_changing_their_scope():
    assert source_values(variant='reordered',indices=(0,3))==[True,True]


def test_false_collective_premise_does_not_run_joint_causal_or_political_content():
    assert source_values(all_false=True,variant='unknown_single')==[True,False]
    assert source_values(all_false=True,variant='unknown_remaining')==[True,False]
    with pytest.raises(ValueError,match='Unknown'):source_values(all_false=True,variant='unknown_scope',indices=(0,))


def test_required_joint_causality_and_remaining_content_cannot_be_skipped_when_premise_holds():
    assert source_values(remaining=False,indices=(0,))==[False]
    assert source_values(variant='unreviewed_single',indices=(0,))==[False]
    with pytest.raises(ValueError,match='Unknown'):source_values(variant='unknown_single',indices=(0,))
    with pytest.raises(ValueError,match='Unknown'):source_values(variant='unknown_remaining',indices=(0,))


def test_unknown_conditional_history_and_out_of_family_reading_are_distinct():
    with pytest.raises(ValueError,match='Unknown'):source_values(variant='unknown_history',indices=(0,))
    assert source_values(indices=(4,))==[False]


def test_attribution_preserves_context_without_executing_the_remaining_political_content():
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]


def test_collective_higher_order_template_keeps_rank_two():
    doc=deepcopy(document(CORE));d=next(d for d in doc['declarations'] if d['name']=='iaqattribution')
    code=d['body']['arguments'][2];assert code['rank']==2;code['rank']=1
    with pytest.raises(ValueError):parse(format_graph(doc,'compact'))


def test_uncached_generic_baseline_parent_preservation_and_reproducible_artifacts():
    assert values(memoize=False)==values()
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert not alignment()['collective_conditional_unfilled'] and alignment()['remaining_political_content_unfilled']
    assert not alignment()['adds_new_text_coverage']
    assert all((ROOT/p).read_text(encoding='utf-8')==text for p,text in build().items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
