from itertools import product
import pytest
from scripts.check_anchored_ability import values,result_for
from scripts.compose_anchored_ability import ROOT,build

@pytest.mark.parametrize('speaker,hearers,context,success,eligible',list(product((False,True),repeat=5)))
def test_bad_references_prove_neither_ability_nor_inability_nor_only_eligibility(speaker,hearers,context,success,eligible):
    valid=speaker and hearers and context
    assert values(speaker=speaker,hearers=hearers,context=context,success=success,eligible=eligible)==result_for(valid,success,not success,eligible)

@pytest.mark.parametrize('variant',('extra_hearer','missing_hearer'))
def test_the_whole_audience_matches_at_the_anchor(variant):
    assert values(variant=variant)==result_for(False,True,False,False)

@pytest.mark.parametrize('variant',('alias_references','later_audience'))
def test_reference_identity_is_not_syntax_identity_or_equality_at_every_situation(variant):
    assert values(variant=variant)==result_for(True,True,False,False)

def test_empty_matching_audiences_are_aligned_but_not_a_nonempty_presentation():
    assert values(variant='empty_audience')==result_for(True,False,True,False)

@pytest.mark.parametrize('variant',('unknown_speaker','unknown_context','unknown_hearers','unknown_availability'))
def test_unknown_references_can_be_described_but_not_assumed_false(variant):
    assert values(variant=variant,indices=(7,))==[True]
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(1,))

def test_raw_inability_does_not_repair_an_incorrect_reference():
    assert values(speaker=False,available=False)==result_for(False,False,True,False)

def test_valid_references_do_not_complete_an_absent_assessment():
    assert values(selected=False)==result_for(True,False,False,False)

def test_cached_and_uncached_results_agree():
    assert values(memoize=False,indices=(0,1,2,7))==values(indices=(0,1,2,7))

def test_documents_reproduce_and_preserve_previous_definitions():
    from noema.constructed import parse
    from scripts.compose_anchored_ability import PARENT,EXAMPLE
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'));child=parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])]==parent['declarations']

def test_reference_evaluation_cannot_be_hidden_inside_a_quote_of_the_same_rank():
    from scripts.check_anchored_ability import lower_rank_refused
    assert lower_rank_refused()
