from itertools import product
import pytest
from scripts.check_choice_permissions import ACTS, values, quotation_mutation
from scripts.compose_choice_permissions import ROOT, build

@pytest.mark.parametrize('missing,denied,opposed,obeys', list(product((False, True), repeat=4)))
def test_missing_choices_cannot_be_hidden_by_removing_candidates(missing, denied, opposed, obeys):
    actual=values(missing=('f',) if missing else (),denied=('f',) if denied else (),
        opposed=('f',) if opposed else (),obeys=obeys)
    allowed=missing or not (denied or opposed)
    assert actual==[not missing,allowed,not missing and allowed,True,obeys]

@pytest.mark.parametrize('activity', tuple(ACTS))
def test_each_combination_of_topic_and_extent_is_required(activity):
    assert values(missing=(activity,))[:3]==[False,True,False]
    assert values(denied=(activity,))[:3]==[True,False,False]

@pytest.mark.parametrize('topics,extents,missing', [
    (('x',),('x','y'),('e','f')), (('x','y'),('x',),('d','f')),
    (('x',),('y',),('c','e','f')), ((),('x','y'),tuple(ACTS)),
    (('x','y'),(),tuple(ACTS))])
def test_unwanted_choices_are_not_silently_required(topics,extents,missing):
    assert values(topics=topics,extents=extents,missing=missing,denied=missing)[:3]==[True]*3

@pytest.mark.parametrize('variant', ('wrong_source','wrong_person','wrong_role','wrong_activity','wrong_point'))
def test_permission_cannot_be_borrowed_from_different_norm_fields(variant):
    assert values(variant=variant)==[True,False,False,True,True]

@pytest.mark.parametrize('variant,index', [('unknown_permission',2),('unknown_obedience',4),('unknown_scope',0)])
def test_quote_construction_does_not_execute_unknown_contents(variant,index):
    assert values(variant=variant,indices=(3,))==[True]
    with pytest.raises(ValueError,match='Unknown'): values(variant=variant,indices=(index,))

@pytest.mark.parametrize('kind', ('reversed','duplicate','omit','permission_as_directive','obedience_as_assertion','swapped_contents'))
def test_quote_order_and_both_forces_are_preserved(kind):
    assert quotation_mutation(kind)==[False]

def test_empty_population_does_not_assert_an_addressee_exists():
    assert values(people=(),missing=tuple(ACTS))[:3]==[True]*3

def test_all_selected_people_receive_the_same_scope_guarantee():
    assert values(people=('p','q'))[:3]==[True]*3

def test_cached_and_uncached_results_agree():
    assert values(memoize=False)==values()

def test_stored_documents_reproduce():
    assert all((ROOT / name).read_text(encoding='utf-8')==body for name,body in build().items())

@pytest.mark.parametrize('person', ('p','q'))
def test_permission_for_one_person_does_not_supply_another(person):
    assert values(people=('p','q'),denied_pairs=((person,'f'),))[:3]==[True,False,False]

def test_permission_denied_outside_the_population_does_not_restrict_selected_people():
    assert values(people=('p',),denied_pairs=(('q','f'),))[:3]==[True,True,True]
