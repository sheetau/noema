from itertools import product
import pytest
from scripts.check_restricted_utterance import values,attribution,alignment,lower_rank_refused,source_document
from scripts.compose_restricted_utterance import ROOT,PARENT,SOURCE,CORE,build


@pytest.mark.parametrize('bits',list(product((False,True),repeat=5)))
def test_the_same_quoted_references_precede_the_necessary_qualification(bits):
    speaker,hearers,context,success,eligible=bits
    assert values(speaker=speaker,hearers=hearers,context=context,success=success,eligible=eligible)==[
        speaker and hearers and context and (not success or eligible),True]


@pytest.mark.parametrize('variant',('criterion_wrong_person','criterion_wrong_anchor','wrong_audience_anchor','extra_hearer','missing_hearer'))
def test_qualification_and_audience_use_the_same_actor_and_anchor(variant):
    assert values(variant=variant,eligible=True)==[False,True]


@pytest.mark.parametrize('variant',('alias_references','later_audience','empty_population'))
def test_aliases_and_anchor_relative_audiences_without_an_existence_claim(variant):
    assert values(variant=variant,eligible=True)==[True,True]


def test_necessary_condition_does_not_add_the_converse_or_inability_evidence():
    assert values(success=False,eligible=True)==[True,True]
    assert values(selected=False,eligible=False)==[True,True]
    assert values(available=False,eligible=False)==[True,True]


@pytest.mark.parametrize('variant',('unknown_criterion','unknown_speaker','unknown_context','unknown_hearers','unknown_availability'))
def test_closed_annotation_can_keep_unknown_qualification_and_reference_inputs(variant):
    assert values(variant=variant,indices=(1,))==[True]
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(0,))


@pytest.mark.parametrize('path',(CORE,SOURCE))
def test_source_annotation_keeps_author_scope_and_context_without_evaluating_the_template(path):
    assert attribution(path)==[True]
    for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]


def test_parent_source_is_preserved_and_qualification_words_are_not_counted():
    old=source_document(PARENT);new=source_document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements']
    assert [s['text'] for s in alignment()['segments']]==['nur derjenige','kann das sagen']
    assert not alignment()['qualification_lexemes_counted']


def test_rank_and_uncached_evaluation():
    assert lower_rank_refused()
    assert values(eligible=True,memoize=False)==[True,True]


def test_documents_reproduce():
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
