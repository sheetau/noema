import pytest
from scripts import check_thought_correspondence as check


@pytest.fixture(scope='module')
def contrasted():return check.contrasts()


def test_all_two_item_profiles_and_correspondence_relations():
    assert check.coverage_checks()['combinations']==256


def test_exact_extent_including_zero_agreement():
    r=check.extent_checks()
    assert r['combinations']==64 and r['empty_agreement_extent_allowed']>0


def test_distinct_items_and_many_to_one_correspondence(contrasted):
    for name in ('baseline','same_item','many_to_one'):assert contrasted['cases'][name]==[True]


def test_shared_item_alone_does_not_hide_unmatched_content(contrasted):
    assert contrasted['cases']['unmatched_right']==[False]


def test_silence_is_not_positive_content_agreement(contrasted):
    for name in ('empty_both','missing_first','missing_second'):assert contrasted['cases'][name]==[False]


def test_matching_is_required_in_both_directions(contrasted):
    assert contrasted['cases']['one_way']==[False]


def test_topic_document_and_context_must_be_shared(contrasted):
    for name in ('wrong_topic','wrong_scene','wrong_document','split_match_context'):assert contrasted['cases'][name]==[False]


def test_unknown_comparisons_are_not_guessed(contrasted):
    assert contrasted['unknown_inputs_refused']


def test_source_question_uses_the_definition_and_can_express_zero_agreement():
    r=check.source_checks()
    assert r['contrasts']['zero_agreement']==[True]
    assert r['presentation_without_evaluating_comparison']


def test_opaque_agreement_primitive_is_replaced_without_changing_other_meanings():
    r=check.structure()
    assert r['replaced_primitive']=='hzkv' and r['previous_statements_preserved']==23


def test_alignment_remains_inside_the_existing_footnote_range():
    assert check.alignment()['segments'][0]['source']=='wiefern der Zufall Einstimmigkeit der Gedanken zuwege bringen könne.'
