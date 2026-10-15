from itertools import product
import pytest
from scripts.check_interpreted_depiction import generic_values,values,attribution,lower_rank_refused,alignment,document
from scripts.compose_interpreted_depiction import ROOT,PARENT,SOURCE,CORE,build


@pytest.mark.parametrize('bits',list(product((False,True),repeat=3)))
def test_the_recorded_target_is_evaluated_instead_of_a_separately_supplied_content(bits):
    mapped,target,arbitrary=bits
    assert generic_values(mapped,target,arbitrary)==[mapped and target,mapped and arbitrary,True]


@pytest.mark.parametrize('variant',('other_person','other_anchor','other_node','other_author','other_mapping_context','reversed_mapping'))
def test_generic_mapping_and_target_application_have_separate_contexts(variant):
    result=generic_values(variant=variant)
    assert result==[False,variant in ('other_person','other_anchor'),True]


def test_unknown_generic_target_is_still_quotable():
    assert generic_values(variant='unknown_target',indices=(2,))==[True]
    with pytest.raises(ValueError,match='Unknown'):generic_values(variant='unknown_target',indices=(0,))


@pytest.mark.parametrize('bits',list(product((False,True),repeat=6)))
def test_source_qualification_uses_the_intended_property_without_asserting_the_depiction(bits):
    mapped,target,remaining,owned,success,literal=bits
    assert values(mapped=mapped,target=target,remaining=remaining,owned=owned,success=success,literal_fear=literal)==[
        mapped and (not success or owned and target and remaining),mapped and target and remaining,owned,True,mapped,target,not literal]


@pytest.mark.parametrize('variant',('other_node','other_author','other_mapping_context','reversed_mapping'))
def test_source_mapping_cannot_use_another_author_node_context_or_direction(variant):
    assert values(variant=variant)==[False,False,True,True,False,True,False]


@pytest.mark.parametrize('variant',('other_target_person','other_target_anchor'))
def test_the_interpreted_property_is_for_the_same_candidate_and_anchor(variant):
    assert values(variant=variant)==[False,False,True,True,True,False,False]


@pytest.mark.parametrize('flags',(dict(speaker=False),dict(hearers=False),dict(context=False)))
def test_the_interpretation_does_not_override_the_quoted_reference_checks(flags):
    assert values(**flags)==[False,True,True,True,True,True,False]


def test_failed_ability_or_an_empty_population_cannot_establish_a_missing_mapping():
    assert values(mapped=False,success=False)==[False,False,True,True,False,True,False]
    assert values(variant='empty_population',mapped=False,indices=(0,))==[False]


def test_source_qualification_does_not_evaluate_the_literal_fear_or_optics():
    assert values(variant='unknown_literal_fear',indices=(0,1,2,3,4,5))==[True]*6
    with pytest.raises(ValueError,match='Unknown'):values(indices=(7,))


@pytest.mark.parametrize('variant,index',(('unknown_target',0),('unknown_mapping',0),('unknown_literal_fear',6)))
def test_unknown_interpretations_are_not_silently_completed(variant,index):
    assert values(variant=variant,indices=(3,))==[True]
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(index,))


@pytest.mark.parametrize('path',(CORE,SOURCE))
def test_attribution_keeps_the_open_template_without_execution(path):
    assert attribution(path)==[True]
    for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]


def test_source_history_and_explicitly_unresolved_interpretation_are_preserved():
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1] and len(new['statements'])==len(old['statements'])
    assert alignment()['intended_meaning_open'] and not alignment()['figurative_reading_confirmed']


def test_rank_limits():assert lower_rank_refused()


def test_uncached_evaluation():assert values(memoize=False,indices=(0,1))==[True,True]


def test_documents_reproduce():
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
