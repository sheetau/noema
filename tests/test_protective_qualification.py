from copy import deepcopy
import pytest
from noema.constructed import parse,format_graph
from scripts.check_protective_qualification import values,attribution,full_domain_refused,binding_structure,document,alignment
from scripts.compose_protective_qualification import ROOT,PARENT,SOURCE,CORE,build


@pytest.mark.parametrize('variant',('baseline','other_actor','other_group','other_anchor','wrong_community',
    'wrong_source','wrong_plan','wrong_person','other_plan_failed','empty_commands'))
def test_source_calls_the_actual_plan_command_and_protection_conditions(variant):
    assert values(variant)==[variant=='baseline']


def test_number_threshold_is_not_invented_and_a_missing_members_compliance_matters():
    assert values(threshold=2)==[False]
    assert values(flags=(True,True,False))==[False]


def test_the_same_group_can_witness_protection_and_the_remaining_qualification():
    assert values(indices=(1,3))==[True,True]


@pytest.mark.parametrize('variant',('wrong_residual_actor','wrong_residual_group','wrong_residual_community','wrong_residual_anchor','residual_false'))
def test_residual_qualification_retains_actor_group_community_and_anchor(variant):
    assert values(variant,indices=(3,))==[False]


@pytest.mark.parametrize('variant,index',(('unknown_provider',0),('unknown_residual',3)))
def test_unknown_inputs_remain_quotable_but_do_not_become_negative_facts(variant,index):
    assert values(variant,indices=(2,),restricted=False)==[True]
    with pytest.raises(ValueError,match='Unknown'):values(variant,indices=(index,))


def test_unbounded_command_descriptions_are_not_silently_sampled():assert full_domain_refused()


def test_actual_source_bindings_keep_all_inputs_on_the_same_candidate():assert binding_structure()


@pytest.mark.parametrize('path',(SOURCE,CORE))
def test_attribution_preserves_the_template_without_evaluating_it(path):
    assert attribution(path)==[True]
    for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]


def test_history_and_residual_meaning_are_preserved():
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert alignment()['residual_qualification_open'] and not alignment()['semantic_completion']


def test_the_source_template_cannot_hide_evaluation_in_a_lower_quote():
    doc=deepcopy(document(CORE))
    definition=next(d for d in doc['declarations'] if d['name']=='hzxattribution')
    definition['body']['arguments'][2]['rank']=1
    with pytest.raises(ValueError,match='strictly lower ranks'):parse(format_graph(doc,'compact'))


def test_documents_reproduce():
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
