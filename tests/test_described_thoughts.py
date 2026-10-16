import pytest
from scripts import check_described_thoughts as check


@pytest.fixture(scope='module')
def quotes():return check.quote_checks()


def test_alpha_normalization_preserves_the_same_description(quotes):
    assert quotes['contrasts']['same']==quotes['contrasts']['alpha']==[True]


def test_negation_subject_and_predicate_are_not_discarded(quotes):
    for key in ('negative','other_subject','other_predicate'):assert quotes['contrasts'][key]==[False]


def test_asserting_asking_and_directing_remain_distinct(quotes):
    for key in ('question','directive'):assert quotes['contrasts'][key]==[False]


def test_quantification_scope_and_conditional_direction_survive(quotes):
    for key in ('universal_existential','scope','condition_direction'):assert quotes['contrasts'][key]==[False]


def test_matching_descriptions_does_not_execute_their_unknown_contents(quotes):
    assert quotes['contents_not_executed']


def test_equal_sampled_truth_is_not_equal_description(quotes):
    assert quotes['sampled_truth_equality_does_not_merge_descriptions']


def test_nonmessage_quotations_are_rejected_including_answer_questions(quotes):
    assert quotes['incompatible_description_sorts_refused']==3


def test_all_profiles_and_relations_respect_the_bridge():
    r=check.bridge_checks()
    assert r['combinations']==512 and r['bridge_implies_extent_agreement']


def test_explicit_asymmetric_criterion_keeps_argument_topic_and_context_order():
    r=check.adapter_checks()
    assert r['asymmetric_criterion_preserved'] and r['topic_and_context_forwarded']
    assert r['unknown_criterion_refused']


def test_source_question_requires_an_explicit_comparison_and_bridge():
    r=check.source_checks()
    assert r['contrasts']['different_unbridged']==[False,False,True]
    assert r['contrasts']['different_bridged']==[True,False,False]
    assert r['unknown_description_refused']


def test_extension_preserves_existing_statements_meanings_and_signature():
    r=check.structure()
    assert r['new_primitives']==0 and r['new_definitions']==7


def test_no_new_source_range_is_claimed():
    assert check.alignment()['segments'][0]['source'].startswith('wiefern')
