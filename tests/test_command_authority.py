from itertools import product
import pytest
from scripts.check_command_authority import core_values,integration_values,full_domain_refused
from scripts.compose_command_authority import ROOT,build


@pytest.mark.parametrize('flags',list(product((False,True),repeat=5)))
def test_root_each_delegation_power_and_each_edge_are_independently_required(flags):
    assert core_values(flags)==[all(flags),True]


@pytest.mark.parametrize('variant',('empty','wrong_end','no_root','repeat','cycle','reversed','wrong_institution','wrong_group',
    'wrong_person','wrong_role','wrong_activity','wrong_code','wrong_sign','wrong_anchor'))
def test_the_same_scoped_instruction_has_a_nonrepeating_rooted_path_to_the_commander(variant):
    assert core_values(variant=variant)==[False,True]


@pytest.mark.parametrize('variant',('direct_root','longer'))
def test_direct_and_longer_authority_paths_are_expressible(variant):
    assert core_values(variant=variant)==[True,True]


def test_direct_root_does_not_require_any_delegation():
    assert core_values((True,False,False,False,False),variant='direct_root')==[True,True]


@pytest.mark.parametrize('field',('institution','group','person','role','activity','code','sign','anchor'))
def test_a_valid_root_cannot_cover_a_delegation_for_a_different_instruction(field):
    assert core_values(variant='edge_wrong_'+field)==[False,True]


def test_core_quotation_does_not_evaluate_unknown_authority():
    assert core_values(variant='unknown_authority',indices=(1,))==[True]
    with pytest.raises(ValueError,match='Unknown'):core_values(variant='unknown_authority',indices=(0,))


def test_uncached_delegation_path_agrees():
    assert core_values(memoize=False)==[True,True]


@pytest.mark.parametrize('variant',('baseline','no_authority','no_delegation_power','missing_delegation','wrong_person','wrong_plan_path'))
def test_authority_does_not_follow_from_actual_conformity(variant):
    assert integration_values(variant)==([True]*3 if variant=='baseline' else [True,False,False])


@pytest.mark.parametrize('variant',('baseline','no_authority'))
def test_authority_is_connected_to_the_actual_community_protection_condition(variant):
    assert integration_values(variant,indices=(5,15))==[True,variant=='baseline']


@pytest.mark.parametrize('variant',('unknown_authority','unknown_path'))
def test_full_quoted_condition_keeps_unknown_authority_inputs(variant):
    assert integration_values(variant,indices=(16,),restricted=False)==[True]
    with pytest.raises(ValueError,match='Unknown'):integration_values(variant,indices=(14,))


def test_unbounded_action_descriptions_remain_unbounded():
    assert full_domain_refused()


def test_saved_documents_reproduce():
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
