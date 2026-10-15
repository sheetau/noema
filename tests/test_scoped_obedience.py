from itertools import product
import pytest
from scripts.check_scoped_obedience import values,full_domain_refused
from scripts.compose_scoped_obedience import ROOT,build

@pytest.mark.parametrize('bits',list(product((False,True),repeat=6)))
def test_current_requirements_and_actual_compliance_are_independent(bits):
    a,b,na,nb,la,lb=bits
    assert values(bits)==[True,a and b and na and not nb,a and b and la and not lb,True]

@pytest.mark.parametrize('variant',('wrong_source','wrong_person','wrong_role','wrong_activity','wrong_description','wrong_sign','wrong_anchor','conflicting'))
def test_matching_truth_does_not_replace_requirement_identity(variant):
    assert values(variant=variant)==[True,False,False,True]

@pytest.mark.parametrize('variant,expected',[
    ('baseline',True),('empty_items',False),('unlisted_activity',False),('unlisted_description',False),('unlisted_sign',False),
    ('unlisted_role',False),('other_source',True),('other_person',True),('other_context',True),('outside_role',True)])
def test_diagnostic_coverage_has_exact_source_person_context_and_role_scope(variant,expected):
    assert values(variant=variant,restricted=True,indices=(3,))==[expected]

def test_empty_list_is_complete_only_when_no_scoped_requirements_exist():
    assert values(variant='empty_items',restricted=True,indices=(1,3,4))==[True,False,False]
    assert values((False,False,False,False,False,False),variant='empty_items',restricted=True,indices=(1,3,4))==[True,True,True]

def test_full_domain_is_not_silently_replaced_by_a_finite_list():
    assert full_domain_refused()

@pytest.mark.parametrize('variant',('unknown_execution','unknown_requirement'))
def test_constructing_quoted_directives_does_not_evaluate_their_contents(variant):
    assert values(variant=variant,indices=(0,5))==[True,True]
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(1,))

def test_requirement_coverage_does_not_execute_the_commanded_actions():
    assert values(variant='unknown_execution',restricted=True,indices=(3,))==[True]

def test_cached_and_uncached_compliance_agree():
    assert values(memoize=False)==values()

def test_stored_examples_reproduce_and_opaque_obedience_is_removed():
    from noema.constructed import parse
    from scripts.compose_scoped_obedience import EXAMPLE
    assert all((ROOT/path).read_text(encoding='utf-8')==body for path,body in build().items())
    names={d['name'] for d in parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))['declarations']}
    assert 'jdobeys' not in names

@pytest.mark.parametrize('a,b,la,lb',list(product((False,True),repeat=4)))
def test_full_compliance_content_in_the_explicit_three_description_diagnostic(a,b,la,lb):
    assert values((a,b,True,False,la,lb),restricted=True,indices=(3,4))==[True,a and b and la and not lb]

@pytest.mark.parametrize('actual',(False,True))
def test_conflicting_commands_can_be_fully_listed_but_cannot_both_be_fulfilled(actual):
    assert values((True,True,actual,False,actual,False),variant='conflicting',restricted=True,indices=(3,4))==[True,False]

def test_successor_preserves_the_permission_and_choice_definitions():
    from noema.constructed import parse
    from scripts.compose_scoped_obedience import EXAMPLE,PARENT,INHERITED,LIBRARY
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    child={d['name']:d for d in parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))['declarations']}
    for declaration in parent['declarations']:
        if declaration['name'] not in ('jdobeys','jdobedience','jdquoted'):
            assert child[declaration['name']]==declaration
    old={d['name']:d for d in parse((ROOT/INHERITED).read_text(encoding='utf-8'))['declarations']}
    library=parse((ROOT/LIBRARY).read_text(encoding='utf-8'))
    assert all(d['kind']=='definition' for d in library['declarations'])
    assert [d for d in library['declarations'] if d['name'] in ('rpl','rpm')]==[old['rpl'],old['rpm']]
