from copy import deepcopy
from itertools import product
import pytest
from noema.constructed import parse,format_graph
from scripts.check_assigned_formation import values,source_values,attribution,binding_structure,document,alignment,CONTRASTS
from scripts.compose_assigned_formation import ROOT,PARENT,SOURCE,CORE,build


@pytest.mark.parametrize('bits',list(product((False,True),repeat=7)))
def test_assignment_member_roles_and_command_are_independent_of_actual_success(bits):
    flags,actual=bits[:6],bits[6]
    assert values(flags,actual)==[all(flags[:4]),all(flags),actual,True]


@pytest.mark.parametrize('variant',CONTRASTS)
def test_the_same_institution_group_beneficiary_mission_and_anchor_are_required(variant):
    assert values(variant=variant)==[False,False,False,True]


def test_a_commander_outside_the_member_list_can_hold_the_groups_command_role():
    assert values()==[True,True,False,True]
    assert values(variant='leader_other_group')==[True,False,False,True]


def test_missions_with_equal_truth_values_do_not_automatically_share_an_assignment():
    assert values(actual=True,variant='alias_assigned',indices=(0,2,4))==[False,True,True]


def test_unknown_mission_outcome_does_not_prevent_evaluating_its_assignment():
    assert values(variant='unknown_mission',indices=(0,1,3))==[True]*3
    with pytest.raises(ValueError,match='Unknown'):values(variant='unknown_mission',indices=(2,))


@pytest.mark.parametrize('variant',('unknown_members','unknown_assignment','unknown_responsibilities'))
def test_unknown_organization_relations_are_not_filled_with_false(variant):
    assert values(variant=variant,indices=(3,))==[True]
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(0,))


@pytest.mark.parametrize('bits',list(product((False,True),repeat=4)))
def test_the_actual_source_qualification_keeps_formation_and_remainder_separate(bits):
    formed,leader,remaining,actual=bits
    assert source_values((formed,True,True,True,leader,True),actual,remaining)==[
        formed and leader,formed and leader and remaining,actual,True]


@pytest.mark.parametrize('variant',('other_institution_selection','other_members_selection'))
def test_the_source_cannot_use_another_institution_or_member_scope(variant):
    assert source_values(variant=variant)==[False,False,False,True]


@pytest.mark.parametrize('variant',('other_remaining_actor','other_remaining_group','other_remaining_community','other_remaining_anchor'))
def test_remaining_conditions_are_for_the_same_candidate_and_community(variant):
    assert source_values(variant=variant)==[True,False,False,True]


def test_unknown_remaining_condition_is_not_silently_dropped():
    assert source_values(variant='unknown_remaining',indices=(0,3))==[True,True]
    with pytest.raises(ValueError,match='Unknown'):source_values(variant='unknown_remaining',indices=(1,))


@pytest.mark.parametrize('path',(SOURCE,CORE))
def test_attribution_keeps_the_open_mission_and_remainder_without_executing_them(path):
    assert attribution(path)==[True]
    for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]


def test_history_binding_and_open_military_meaning_are_explicit():
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert binding_structure()
    assert alignment()['military_mission_open'] and not alignment()['semantic_completion']


def test_lower_quotation_rank_is_rejected():
    doc=deepcopy(document(CORE));decl=next(d for d in doc['declarations'] if d['name']=='hzyattribution')
    decl['body']['arguments'][2]['rank']=1
    with pytest.raises(ValueError,match='strictly lower ranks'):parse(format_graph(doc,'compact'))


def test_uncached_values_agree():assert values(memoize=False)==[True,True,False,True]


def test_documents_reproduce():
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
