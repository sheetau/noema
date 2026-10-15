from copy import deepcopy
from itertools import product
import json

import pytest

from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from scripts.check_collective_office import (values,truth_table,pivotal,source_values,source_fixture,attribution,
    document,interpretation,CONTRASTS,DOMAIN,SCENES,alignment)
from scripts.compose_collective_office import ROOT,PARENT,EXAMPLE,SOURCE,CORE,BASIS,build,basis


@pytest.mark.parametrize('count,table',[(n,t) for n in (2,3) for t in range(1<<(1<<n))])
def test_every_small_decision_rule_matches_independent_bit_flip_influence(count,table):
    impact=pivotal(count,table)
    assert values(count,table)==[all(impact),impact[0],impact[1],True,True]


@pytest.mark.parametrize('variant',CONTRASTS)
def test_holders_role_order_human_participation_and_scope_must_match(variant):
    assert values(variant=variant)[0] is False


@pytest.mark.parametrize('rule',('majority','unanimity','any','parity'))
def test_shared_authority_does_not_require_majority_voting(rule):
    assert values(table=truth_table(3,rule))==[True]*5


@pytest.mark.parametrize('count',(0,1))
def test_empty_or_one_person_office_is_not_plural(count):
    assert values(count=count,table=truth_table(count,'first'))==[False,count==1,False,True,True]


def test_a_nominal_committee_with_one_decider_is_not_shared_authority():
    assert values(table=truth_table(3,'first'))==[False,True,False,True,True]
    assert values(table=truth_table(3,'constant'))==[False,False,False,True,True]


def test_position_changes_preserve_the_declared_identity_of_the_decider():
    # Under the same positional rule, reversing the two holders changes whose
    # choice matters. Renaming a participant cannot make a second decider.
    assert values(count=2,table=truth_table(2,'first'))==[False,True,False,True,True]
    assert values(count=2,table=truth_table(2,'first'),variant='reverse_order')==[False,False,True,True,True]


def test_unrelated_roles_and_many_nonparticipants_do_not_expand_ballot_domain():
    assert values(variant='outside_cycle')==[True]*5
    doc=deepcopy(document(EXAMPLE));doc['statements']=doc['statements'][:1]
    extended=DOMAIN+tuple('extra'+str(i) for i in range(10))
    result=evaluate_document(doc,individuals=extended,situations=SCENES,primitives=interpretation(),
        memoize_definitions=True,memoize_expressions=True,max_steps=2_000_000)
    assert result==[dict(kind='ask',value=True)]


@pytest.mark.parametrize('civic,allowed,qualified',list(product((False,True),repeat=3)))
def test_shared_office_civic_basis_and_actual_speech_contrast_are_composed(civic,allowed,qualified):
    denied=not civic or not allowed
    assert source_values(civic=civic,allowed=allowed,qualified=qualified)==[True,civic,qualified and denied,True,denied]


def test_excluding_a_polity_is_not_evidence_that_an_included_polity_lacks_permission():
    assert source_values(table=truth_table(3,'first'),allowed=True)==[False,False,True,True,True]


def test_the_collective_is_not_coerced_into_the_human_speaker_and_misreference_fails():
    doc,kwargs=source_fixture()
    assert kwargs['primitives']['aa']('speaker') is True
    assert kwargs['primitives']['aa']('other') is False
    assert all(kwargs['primitives']['aa'](p) for p in ('p1','p2','p3'))
    assert source_values(variant='wrong_polity_reference')==[True,True,False,True,False]


@pytest.mark.parametrize('variant',('unknown_rule','unknown_holders','unknown_civic','unknown_norm'))
def test_unknown_inputs_can_be_quoted_but_cannot_be_completed(variant):
    assert source_values(variant=variant,indices=(3,))==[True]
    with pytest.raises(ValueError,match='Unknown'):source_values(variant=variant,indices=(2,))


@pytest.mark.parametrize('path',(SOURCE,CORE))
def test_source_annotation_is_not_an_evaluation_of_political_classification(path):
    assert attribution(path)==[True]
    for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]


def test_source_keeps_history_and_civic_requirements_explicit():
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert alignment()['civic_basis_open'] and not alignment()['semantic_completion']
    assert [s['text'] for s in alignment()['segments']]==['Freistaat']


def test_source_quotation_cannot_erase_the_existing_reference_evaluation_rank():
    doc=deepcopy(document(CORE))
    node=next(d for d in doc['declarations'] if d['name']=='iabattribution')['body']['arguments'][2]
    assert node['rank']==2
    node['rank']=1
    with pytest.raises(ValueError):parse(format_graph(doc,'compact'))


def test_uncached_evaluation_and_generated_documents_agree():
    assert values(memoize=False)==values()
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
