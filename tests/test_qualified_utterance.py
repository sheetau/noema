from itertools import product
import pytest
from scripts.check_qualified_utterance import values,attribution,alignment,source_document
from scripts.compose_qualified_utterance import ROOT,PARENT,SOURCE,CORE,build


@pytest.mark.parametrize('bits',list(product((False,True),repeat=6)))
def test_ownership_use_other_guidance_assessment_and_remaining_condition(bits):
    owned,used,guided,assessed,remaining,success=bits
    capable=owned and used and not guided and assessed
    assert values(owned=owned,used=used,guided=guided,assessed=assessed,remaining=remaining,success=success)==[
        not success or capable and remaining,capable and remaining,capable,True]


@pytest.mark.parametrize('variant',('other_owner','other_faculty','other_capable_person','other_ability_anchor',
    'ownership_only_at_anchor','no_method','unassessed_extra_method','selected_nonoutcome','not_person'))
def test_same_owned_faculty_and_assessed_capability_are_required(variant):
    assert values(variant=variant)==[False,False,False,True]


@pytest.mark.parametrize('variant',('self_guidance','other_guided_actor','other_guided_act','alias_references','later_audience'))
def test_unrelated_guidance_and_equivalent_references_do_not_remove_capacity(variant):
    assert values(variant=variant)==[True,True,True,True]


@pytest.mark.parametrize('flags',(dict(speaker=False),dict(hearers=False),dict(context=False)))
def test_capacity_does_not_override_the_quoted_reference_check(flags):
    assert values(**flags)==[False,True,True,True]


@pytest.mark.parametrize('variant',('criterion_wrong_person','criterion_wrong_anchor'))
def test_remaining_condition_uses_the_same_person_and_anchor(variant):
    assert values(variant=variant)==[False,False,True,True]


@pytest.mark.parametrize('variant,expected',[
    ('baseline',[True,True,True,False,False]),
    ('unassessed_extra_method',[False,True,False,False,False]),
    ('other_capable_person',[False,False,True,True,False]),
    ('no_method',[False,False,True,False,False])])
def test_success_method_full_assessment_other_person_and_actual_use_are_distinct(variant,expected):
    assert values(variant=variant,indices=(2,4,5,6,7))==expected


@pytest.mark.parametrize('variant',('unknown_ownership','unknown_assessment','unknown_criterion'))
def test_unknown_qualification_is_quotable_but_cannot_be_evaluated(variant):
    assert values(variant=variant,indices=(3,))==[True]
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(1,))


@pytest.mark.parametrize('path',(CORE,SOURCE))
def test_attribution_does_not_evaluate_qualification_or_speech(path):
    assert attribution(path)==[True]
    for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]


def test_declarations_and_prior_statements_are_preserved():
    old,new=source_document(PARENT),source_document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert len(new['statements'])==len(old['statements'])
    assert [s['text'] for s in alignment()['segments']]==['nur derjenige','selbst aufgeklärt','kann das sagen']
    assert alignment()['remaining_qualification_open'] and not alignment()['self_emphasis_complete']


def test_uncached_evaluation():
    assert values(memoize=False,indices=(0,1,2))==[True,True,True]


def test_documents_reproduce():
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
