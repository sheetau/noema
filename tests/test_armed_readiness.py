from copy import deepcopy
from itertools import product
import pytest
from noema.constructed import parse,format_graph
from scripts.check_armed_readiness import values,source_values,attribution,binding_structure,document,alignment,CONTRASTS
from scripts.compose_armed_readiness import ROOT,PARENT,SOURCE,CORE,build


@pytest.mark.parametrize('flags',list(product((False,True),repeat=7)))
def test_both_levels_of_methods_and_assessment_must_support_the_same_operation(flags):
    assert values(flags)==[all(flags),False,True]


@pytest.mark.parametrize('current,harm',list(product((False,True),repeat=2)))
def test_readiness_does_not_require_present_fighting_or_present_injury(current,harm):
    assert values(current=current,current_harm=harm)==[True,current,True]


def test_present_action_does_not_supply_an_unavailable_assessed_unit_method():
    assert values((True,False,True,True,True,True,True),current=True)==[False,True,True]


@pytest.mark.parametrize('variant',CONTRASTS)
def test_physical_means_participants_and_unit_cannot_be_taken_from_another_case(variant):
    assert values(variant=variant)==[False,False,True]


@pytest.mark.parametrize('variant',('unknown_effect','unknown_tool_methods','unknown_tool_selection','unknown_unit_methods','unknown_unit_selection'))
def test_unknown_effects_and_capabilities_do_not_become_failure_or_success(variant):
    assert values(variant=variant,indices=(2,))==[True]
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(0,))


@pytest.mark.parametrize('bits',list(product((False,True),repeat=3)))
def test_actual_assignment_definition_and_actual_readiness_are_evaluated_together(bits):
    ready,assigned,remaining=bits
    assert source_values(ready=ready,assigned=assigned,remaining=remaining)==[ready,assigned,True,ready and assigned and remaining,True]


@pytest.mark.parametrize('variant,expected',(
    ('new_scope_extra',[True,True,False,False,True]),('old_scope_extra',[True,False,False,False,True]),
    ('old_future_extra',[True]*5),('other_remaining_community',[True,True,True,False,True])))
def test_the_source_shares_current_members_without_freezing_future_membership(variant,expected):
    assert source_values(variant=variant)==expected


@pytest.mark.parametrize('variant,index',(('unknown_scope',2),('unknown_remaining',3)))
def test_unknown_source_inputs_are_quotable_but_not_completed(variant,index):
    assert source_values(variant=variant,indices=(4,))==[True]
    with pytest.raises(ValueError,match='Unknown'):source_values(variant=variant,indices=(index,))


@pytest.mark.parametrize('path',(SOURCE,CORE))
def test_attribution_does_not_assert_present_fighting_or_qualification(path):
    assert attribution(path)==[True]
    for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]


def test_source_history_and_candidate_interpretation_are_preserved():
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert binding_structure()
    assert not alignment()['military_mission_open'] and not alignment()['semantic_completion']


def test_source_quotation_keeps_required_rank():
    doc=deepcopy(document(CORE));d=next(d for d in doc['declarations'] if d['name']=='hzzattribution')
    d['body']['arguments'][2]['rank']=1
    with pytest.raises(ValueError,match='strictly lower ranks'):parse(format_graph(doc,'compact'))


def test_evaluation_without_memoization_agrees():assert values(memoize=False)==[True,False,True]


def test_documents_reproduce():
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
