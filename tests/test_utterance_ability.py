from itertools import product
import pytest
from scripts.check_utterance_ability import values,expected
from scripts.compose_utterance_ability import ROOT,build

@pytest.mark.parametrize('bits',list(product((False,True),repeat=7)))
def test_ability_keeps_available_plans_outcomes_assessment_and_success_distinct(bits):
    assert values(bits)==expected(bits)

@pytest.mark.parametrize('variant',('empty_events','short_events','extra_events','reversed_events','duplicate_event','other_actor','other_listener',
    'swapped_messages','other_speaker_content','no_order','self_order','two_way_order','empty_audience'))
def test_the_ordered_utterance_requires_the_same_events_speaker_audience_and_messages(variant):
    assert values(variant=variant)==[False,False,False,True,True,True,True]

def test_a_message_can_be_repeated_in_distinct_ordered_events():
    assert values(variant='repeated_message',indices=(0,1))==[True,True]

@pytest.mark.parametrize('variant',('unknown_occurrence','unknown_availability'))
def test_describing_the_realization_goal_does_not_execute_it(variant):
    assert values(variant=variant,indices=(6,))==[True]
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(2,))

def test_necessary_eligibility_does_not_assert_capability_or_existence():
    bits=(False,True,True,True,True,True,True)
    assert values(bits,eligible=True)==[True,True,False,True,True,True,True]

def test_missing_assessment_is_not_confirmed_inability():
    bits=(True,True,True,False,False,True,True)
    assert values(bits)==[True,True,False,False,True,False,True]

def test_success_in_only_one_assessed_outcome_is_not_guaranteed_achievement():
    assert values((True,True,True,True,True,True,False))[2:4]==[False,True]

def test_cached_and_uncached_execution_agree():
    assert values(memoize=False,indices=(0,1,2,3,6))==values(indices=(0,1,2,3,6))

def test_documents_reproduce():
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())

@pytest.mark.parametrize('program',[p for length in range(4) for p in product((0,1),repeat=length)]+[(0,1,0,1)])
def test_sequence_realization_works_for_different_lengths_and_repeated_content(program):
    assert values(program=program,indices=(0,1))==[bool(program)]*2

def test_capability_does_not_require_the_utterance_to_have_already_occurred():
    assert values(variant='current_point',indices=(0,2))==[False,True]
