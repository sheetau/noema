from itertools import product
import pytest
from scripts.check_shared_quotation import values,source_construction,attribution
from scripts.compose_shared_quotation import ROOT,SOURCE,CORE,build

@pytest.mark.parametrize('a,b,c,d',list(product((False,True),repeat=4)))
def test_each_person_has_independent_permission_and_compliance(a,b,c,d):
    assert values((a,b),(c,d))==[a and b,c and d,True]

@pytest.mark.parametrize('variant',('missing_person_command','other_description','other_source','other_anchor','omitted_person_records'))
def test_another_person_or_norm_cannot_supply_compliance(variant):
    assert values(variant=variant)==[True,False,True]

@pytest.mark.parametrize('people', [(),('p',),('q',)])
def test_the_same_audience_is_used_by_both_clauses(people):
    assert values((True,False),(False,True),people=people)==[all(p=='p' for p in people),all(p=='q' for p in people),True]

@pytest.mark.parametrize('variant',('unknown_requirements','unknown_permissions','unknown_execution'))
def test_full_quoted_template_can_be_constructed_without_interpreting_its_contents(variant):
    assert values(variant=variant,indices=(2,),restricted=False)==[True]

def test_the_full_description_domain_is_retained():
    with pytest.raises(ValueError,match='description domain'):values(indices=(1,),restricted=False)

@pytest.mark.parametrize('path',(SOURCE,CORE))
def test_source_quotation_constructs_the_actual_template_without_evaluating_it(path):
    assert source_construction(path)==[True]
    assert attribution(path)==[True] and attribution(path,False)==[False]

@pytest.mark.parametrize('variant',('node','author','scope','context'))
def test_quote_attribution_preserves_its_location_author_and_context(variant):
    assert attribution(variant=variant)==[False]

def test_cache_does_not_change_permission_or_quotation():
    assert values(memoize=False,indices=(0,2))==values(indices=(0,2))

def test_outputs_reproduce():
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())

@pytest.mark.parametrize('variant,expected',[
    ('baseline',[True,True,True]),('other_role',[False,True,False]),('other_topic',[True,False,False])])
def test_actual_source_role_and_topic_are_bound_to_the_same_constructed_public_action(variant,expected):
    from scripts.check_shared_quotation import source_fields
    assert source_fields(variant)==expected

def test_the_public_action_can_be_described_before_the_role_is_evaluated():
    from scripts.check_shared_quotation import source_fields
    assert source_fields('unknown_role',indices=(2,))==[True]
    with pytest.raises(ValueError,match='Unknown role'):source_fields('unknown_role',indices=(0,))
