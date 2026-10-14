import json

import pytest

from noema.grammar import parse
from scripts.check_appointment_terms import REPORT,build_report
from scripts.compose_appointment_terms import ROOT,PARENT,source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_past_appointment_is_independent_of_current_duty_and_performance(result):
    rows=result['finite']['cases']
    assert len(rows)==128
    for row in rows:
        occurred,delegated,appointed,terms,required,current,performed=row['states']
        past=occurred and delegated and appointed and terms
        assert row['results']==[past,past,past and required,required,performed]
    assert result['finite']['standalone_agrees']


def test_terms_cannot_be_borrowed_from_another_event_or_time(result):
    contrasts=result['finite']['binding_and_history_contrasts']
    assert len(contrasts)==29
    for name in ('split_event','split_time','appointment_issuer','appointment_person','appointment_role',
                 'terms_activity','terms_description','terms_polarity'):
        assert contrasts[name]==[False,False,False,True,True]


def test_present_duty_preserves_each_of_its_bindings(result):
    contrasts=result['finite']['binding_and_history_contrasts']
    for field in ('issuer','person','role','activity','time','description','polarity'):
        assert contrasts['norm_'+field]==[True,True,False,False,True]


def test_past_requires_a_shared_valid_ordered_history(result):
    contrasts=result['finite']['binding_and_history_contrasts']
    for name in ('present_only','future_only','foreign_history','history_person','history_time',
                 'cyclic_order','reflexive_order','incomparable_order','nontransitive_order'):
        assert contrasts[name]==[False,False,False,True,True]


def test_named_witness_does_not_impose_uniqueness_on_past_appointment(result):
    assert result['finite']['named_and_existential_witnesses']==[[False,True,True,True,True]]*2
    assert result['finite']['binding_and_history_contrasts']['two_appointments']==[True]*5
    assert result['finite']['laboratory_interpretation']==[True]*5


def test_negative_terms_and_unknown_targets_are_not_treated_as_performance(result):
    assert result['finite']['negative_terms_with_target_actually_true']==[[True]*5]*2
    assert result['finite']['target_not_executed_by_appointment_or_requirement']
    assert result['finite']['unknown_target_refused']
    assert set(result['finite']['unknown_relations_refused'])=={'zh','zi','ia','ic','dg','cf','h7a'}


def test_prior_teaching_description_can_be_shared_with_the_appointment(result):
    assert result['teaching']['same_closed_teaching_description']==[True]*4
    assert result['teaching']['reordered_standard_description']==[False]*4
    assert result['teaching']['target_not_evaluated']
    assert result['teaching']['alternatives_share_one_definition_scope']
    assert result['teaching']['static_specialization']['bound_positions']==[7]


def test_source_and_report_preserve_scope_and_parent(result):
    text,_=source_composed();doc=parse(text)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements']==parent['statements']
    assert len(doc['declarations'])==len(parent['declarations'])+6
    assert result['new_primitives']==result['new_author_statements']==0
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result['alignment']['segments'][0]['text']=='er ist auf diese Bedingung angenommen worden'
    assert result['alignment']['segments'][0]['status']=='partial'
    assert result['roundtrips']
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
