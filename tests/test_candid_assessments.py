from itertools import product
import json

import pytest

from noema.constructed import parse
from scripts.compose_candid_assessments import ROOT,PARENT,LIBRARY,EXAMPLE,BASIS,build,basis
from scripts.check_candid_assessments import RECORDS,values,quotation_case,setup


@pytest.mark.parametrize('first,second,current1,current2,delivered1,delivered2',list(product((False,True),repeat=6)))
def test_current_truth_is_separate_from_own_evaluation_and_full_disclosure(first,second,current1,current2,delivered1,delivered2):
    complete=first and not second and delivered1 and delivered2
    assert values(candidate=(first,second),actual=(current1,current2),delivered=(delivered1,delivered2))==[complete,complete,current2]


@pytest.mark.parametrize('records,scope,expected',[
    ((),(),[False,False,True]),
    (('first',),RECORDS,[False,False,True]),
    (RECORDS,('first',),[False,False,True]),
    (('first',),('first',),[True,False,True]),
    (('second',),('second',),[True,True,True]),
    (('second','first'),RECORDS,[True,True,True]),
    (('first','second','first'),RECORDS,[True,True,True]),
    (('first','second','outside'),RECORDS,[False,False,True]),
])
def test_declared_scope_cannot_be_replaced_by_a_selected_subset(records,scope,expected):
    assert values(records=records,scope=scope)==expected


@pytest.mark.parametrize('variant',('other_person','other_subject','other_criterion','wrong_polarity','wrong_message','other_activity','other_principal'))
def test_judgment_and_signed_message_require_the_same_binding(variant):
    assert values(variant=variant)==[False,False,True]


@pytest.mark.parametrize('first,second',list(product((False,True),repeat=2)))
def test_negative_assessment_is_required_only_for_the_critical_subcase(first,second):
    assert values(signs=(first,second),candidate=(first,second))==[True,not(first and second),True]


@pytest.mark.parametrize('first,second',list(product((False,True),repeat=2)))
def test_speakers_actual_judgments_cannot_be_inferred_from_public_speech(first,second):
    assert values(judgments=(first,second))==[first and second,first and second,True]


@pytest.mark.parametrize('first,second',list(product((False,True),repeat=2)))
def test_empty_candidate_set_does_not_establish_a_personal_assessment(first,second):
    assert values(candidates=(first,second))==[first and second,first and second,True]


@pytest.mark.parametrize('variant,message',[
    ('unknown_scope','Unknown disclosure scope'),('unknown_candidates','Unknown judgment candidates'),('unknown_truth','Unknown criterion evaluation')])
def test_unknown_interpretations_are_not_filled_with_false(variant,message):
    with pytest.raises(ValueError,match=message):values(variant=variant)


def test_signed_message_construction_does_not_evaluate_its_criterion():
    assert quotation_case()==[dict(kind='ask',value=True)]


def test_same_definition_under_another_name_does_not_transfer_a_judgment():
    lookup={d['name']:d for d in setup()['document']['declarations']}
    assert {k:v for k,v in lookup['jdstandardone'].items() if k!='name'}=={
        k:v for k,v in lookup['jdstandardalias'].items() if k!='name'}
    assert values(variant='other_criterion')==[False,False,True]


def test_pure_cache_and_uncached_evaluation_agree():
    assert values(memoize=False)==values()==[True,True,True]


def test_exact_reproduction_and_inherited_definitions():
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    parent={d['name']:d for d in parse((ROOT/PARENT).read_text(encoding='utf-8'))['declarations']}
    library=parse((ROOT/LIBRARY).read_text(encoding='utf-8'))
    additions=[d for d in library['declarations'] if d['name'] not in parent]
    assert len(additions)==7 and all(d['kind']=='definition' for d in additions)
    assert all(d==parent[d['name']] for d in library['declarations'] if d['name'] in parent)
    assert not library['statements']
    assert [s['kind'] for s in parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))['statements']]==['ask']*3
