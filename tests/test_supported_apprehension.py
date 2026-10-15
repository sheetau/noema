from copy import deepcopy
from itertools import product
import pytest
from noema.constructed import parse, format_graph
from scripts.check_supported_apprehension import (values,expected,source_values,attribution,
    full_domain_refused,document,alignment,CONTRASTS)
from scripts.compose_supported_apprehension import ROOT,PARENT,SOURCE,CORE,build


@pytest.mark.parametrize('flags',list(product((False,True),repeat=7)))
def test_fear_and_available_support_are_distinct(flags):
    assert values(flags)==expected(flags)


@pytest.mark.parametrize('bits',list(product((False,True),repeat=3)))
def test_grounds_do_not_require_actual_existence_or_actual_harm(bits):
    grounds,target,harm=bits
    flags=(True,)*6+(grounds,)
    assert values(flags,actual_target=target,actual_harm=harm)==expected(flags,target,harm)


@pytest.mark.parametrize('variant',CONTRASTS)
def test_other_person_reason_context_topic_or_forecast_cannot_supply_support(variant):
    assert values(variant=variant)==[True,False,True,False,False,False,True]


def test_one_supported_episode_cannot_hide_another_unsupported_episode():
    assert values(variant='second_unsupported')==[True,True,True,False,False,False,True]


def test_description_can_be_feared_and_supported_without_executing_its_property():
    assert values(variant='unknown_target',indices=(0,1,2,3,6))==[True,True,False,True,True]
    with pytest.raises(ValueError,match='Unknown'):values(variant='unknown_target',indices=(4,))


@pytest.mark.parametrize('variant',('unknown_available','unknown_support','unknown_experience'))
def test_unknown_relations_do_not_become_negative_evidence(variant):
    assert values(variant=variant,indices=(6,))==[True]
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(3,))


@pytest.mark.parametrize('bits',list(product((False,True),repeat=6)))
def test_actual_source_candidate_connects_grounds_to_utterance_qualification(bits):
    fear,grounds,mapped,remaining,owned,success=bits
    result=source_values(fear=fear,supports=grounds,mapped=mapped,remaining=remaining,owned=owned,success=success)
    target=not fear or grounds
    assert result==[mapped and (not success or owned and target and remaining),mapped and target and remaining,owned,True,mapped,target]


@pytest.mark.parametrize('variant',('other_person','other_reason','other_support_anchor','alias_support','unknown_available','unknown_mapping'))
def test_source_uses_actual_reason_relations_and_mapping(variant):
    assert source_values(variant=variant,indices=(3,))==[True]
    if variant.startswith('unknown'):
        with pytest.raises(ValueError,match='Unknown'):source_values(variant=variant,indices=(0,))
    else:assert source_values(variant=variant,indices=(0,5))==[False,False]


def test_unavailable_reason_does_not_ground_a_fear():
    assert source_values(available=False,indices=(0,5))==[False,False]


def test_full_description_quantification_is_not_silently_replaced_by_two_examples():
    assert full_domain_refused()


@pytest.mark.parametrize('path',(SOURCE,CORE))
def test_candidate_annotation_does_not_execute_its_content(path):
    assert attribution(path)==[True]
    for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]


def test_source_history_and_ambiguity_are_preserved():
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert not alignment()['intended_meaning_open']
    assert not alignment()['figurative_reading_confirmed'] and not alignment()['semantic_completion']
    universal=next(d for d in new['declarations'] if d['name']=='rvy')['body']
    assert universal['kind']=='forall' and universal['sort']['kind']=='description'


def test_candidate_keeps_the_required_quotation_rank():
    doc=deepcopy(document(CORE))
    annotation=next(d for d in doc['declarations'] if d['name']=='hzwattribution')
    annotation['body']['arguments'][2]['rank']=1
    with pytest.raises(ValueError,match='strictly lower ranks'):parse(format_graph(doc,'compact'))


def test_memoization_does_not_change_semantics():assert values(memoize=False)==expected((True,)*7)


def test_documents_reproduce():
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
