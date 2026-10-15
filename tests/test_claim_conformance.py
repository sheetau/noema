from itertools import product
import json
import pytest
from noema.constructed import parse
from scripts.check_claim_conformance import values,document,alignment
from scripts.compose_claim_conformance import ROOT,PARENT,SOURCE,CORE,BASIS,REVIEW,build,basis,reading_review
from scripts.check_thinking_disposition import code_is


@pytest.mark.parametrize('norms',list(product(range(4),repeat=3)))
def test_same_claims_at_current_and_two_comparison_contexts(norms):
    current=norms[0]==3;stable=norms[1:]==(3,3)
    assert values(norms)==[current,True,current,stable,current and stable,True]


@pytest.mark.parametrize('required,fulfilled',list(product(range(4),repeat=2)))
def test_requirement_does_not_entail_actual_fulfillment(required,fulfilled):
    want=required==3 and fulfilled==3
    assert values((required,3,3),fulfilled)==[required==3,fulfilled==3,want,True,want,True]


@pytest.mark.parametrize('variant',('empty_claims','duplicate_claims','omitted_claim'))
def test_incomplete_or_empty_claim_catalogue_is_not_respect(variant):
    assert values(variant=variant)==[False,False,False,False,False,True]


def test_empty_comparison_scope_cannot_prove_stability():
    assert values(variant='empty_cases')==[True,True,True,False,False,True]


def test_favorable_outcomes_never_replace_fulfillment_and_are_not_required_for_it():
    assert values(fulfilled=1,benefit=True)==[True,False,False,True,False,True]
    assert values(fulfilled=3,benefit=False)==[True,True,True,True,True,False]


@pytest.mark.parametrize('variant',('other_person','reversed_binding','alias'))
def test_requirement_for_another_person_order_or_description_is_not_transferred(variant):
    assert values(variant=variant)==[False,True,False,False,False,True]


def test_fulfilling_the_content_for_someone_else_is_not_this_persons_treatment():
    assert values(variant='other_recipient')==[True,False,False,True,False,True]


def test_unknown_treatment_does_not_prevent_separately_stating_the_requirement():
    assert values(variant='unknown_content',indices=(0,3))==[True,True]
    with pytest.raises(ValueError,match='Unknown'):values(variant='unknown_content',indices=(1,))


@pytest.mark.parametrize('variant',('unknown_norm','unknown_scope'))
def test_unknown_requirements_and_inventory_are_not_filled_in(variant):
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant)


@pytest.mark.parametrize('path',(CORE,SOURCE))
def test_source_adapter_anchors_inventory_and_keeps_all_normative_parties(path):
    calls=[]
    assert values(path=path,indices=(6,7),calls=calls)==[True,True]
    assert all(r[1:]==('person','anchor') for r in calls if r[0]=='claims')
    norms=[r for r in calls if r[0]=='norm']
    assert norms and all(r[1:4]==('source','actor','office') and r[5:7]==(('actor','person'),True) for r in norms)
    assert all(code_is(r[4],'jvone') or code_is(r[4],'jvtwo') for r in norms)
    assert values(path=path,variant='nonhuman',indices=(6,7))==[False,False]
    assert values(path=path,fulfilled=0,indices=(6,7))==[True,False]


def test_dynamic_claim_content_requires_rank_one_instead_of_a_rank_zero_policy_cast():
    text=(ROOT/CORE).read_text(encoding='utf-8')
    parse(text+'q[e[r b[p iautreatment]][r b[p iautreatment]]].')
    with pytest.raises(ValueError):parse(text+'q[e[r[p iautreatment]][r[p iautreatment]]].')


def test_reproducible_build_and_no_new_author_assertion_or_coverage():
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements']==old['statements']
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    assert json.loads((ROOT/REVIEW).read_text(encoding='utf-8'))==reading_review()
    assert not alignment()['adds_new_text_coverage'] and alignment()['policy_integration_unfilled']
    assert values(memoize=False)==values()
