from itertools import product
import pytest
from scripts.check_described_apprehension import values,expected,lower_rank_refused
from scripts.compose_described_apprehension import ROOT,build


@pytest.mark.parametrize('bits',list(product((False,True),repeat=7)))
def test_same_aversive_episode_and_anticipated_harm_without_actuality_import(bits):
    flags=bits[:5];target,harm=bits[5:]
    assert values(flags,actual_target=target,actual_harm=harm)==expected(flags,target,harm)


@pytest.mark.parametrize('variant',('other_experiencer','split_episode','other_direction_context','other_affect_episode',
    'other_affect_context','other_prospect_episode','other_prospect_context','other_harmed_person','split_outcome'))
def test_components_cannot_be_collected_from_different_people_states_or_outcomes(variant):
    assert values(variant=variant)==[False,False,True,False,False,True,True,False]


@pytest.mark.parametrize('variant',('reverse_topics','repeat_topics'))
def test_order_and_repetition_do_not_change_a_universal_negative(variant):
    assert values(variant=variant)==expected((True,)*5)


@pytest.mark.parametrize('variant',('alias_only','empty_topics'))
def test_negative_claim_is_only_about_the_explicit_topic_list(variant):
    assert values(variant=variant)==[True,False,True,False,False,True,True,False]


def test_same_extension_does_not_transfer_an_attitude_between_descriptions():
    assert values(variant='alias_attitude')==[False,True,False,False,False,True,True,False]
    assert values(actual_target=True,variant='missing_wings')==expected((True,)*5)


def test_attitude_does_not_evaluate_its_target_description():
    assert values(variant='unknown_target',indices=(0,1,2,5,6))==[True,False,False,True,True]
    with pytest.raises(ValueError,match='Unknown'):values(variant='unknown_target',indices=(3,))


@pytest.mark.parametrize('variant',('unknown_experience','unknown_direction','unknown_adverse'))
def test_unknown_experience_cannot_be_silently_negated(variant):
    assert values(variant=variant,indices=(5,))==[True]
    for index in (0,2):
        with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(index,))


def test_explicit_realization_has_the_correct_quotation_rank():assert lower_rank_refused()


def test_uncached_evaluation():assert values(memoize=False)==expected((True,)*5)


def test_documents_reproduce():
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
