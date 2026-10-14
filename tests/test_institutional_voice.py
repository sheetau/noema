import json

import pytest

from noema.grammar import parse
from scripts.check_institutional_voice import REPORT,build_report
from scripts.compose_institutional_voice import ROOT,PARENT,source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_attributed_voice_and_delegated_role_are_distinct(result):
    rows=result['speech']['cases']
    assert len(rows)==128
    for row in rows:
        voice=all(row['states'][:4]);delegated=voice and all(row['states'][4:])
        assert row['results']==[voice,delegated,delegated,True]
    assert result['speech']['standalone_agrees']
    assert result['speech']['actual_and_constructed_target_agree']


def test_principal_speaker_activity_role_and_message_are_bound_together(result):
    rows=result['speech']['binding_contrasts']
    assert len(rows)==35
    for name in ('voice_person','voice_activity','voice_principal','voice_role','voice_subject','voice_context',
                 'voice_force','voice_alias','delivery_force','delivery_alias','empty_audience','missing_reader'):
        assert rows[name]==[False,False,False,True]
    for name in ('position_person','delegation_role','service_principal'):
        assert rows[name]==[True,False,False,True]


def test_actual_voice_does_not_create_a_requirement(result):
    assert result['speech']['actual_speech_does_not_create_obligation']
    for field in ('principal','person','role','activity','context','description'):
        assert result['speech']['binding_contrasts']['norm_'+field]==[True,True,True,False]


def test_report_truth_inner_truth_and_personal_endorsement_are_independent(result):
    rows=result['reports']['cases']
    assert len(rows)==8
    for row in rows:
        assert row['results']==[True,*row['states'],True]
    assert result['reports']['report_is_assertion']
    assert result['reports']['exact_presented_report_is_evaluated']
    assert result['reports']['institutional_teaching_does_not_create_speech']
    assert result['reports']['institutional_teaching_does_not_require_truth_or_endorsement']


def test_nested_report_retains_the_institution_subject_and_inner_message(result):
    rows=result['reports']['binding_contrasts']
    assert set(rows)=={'principal','subject','context','force','alias'}
    assert all(value==[True,False,True,True,True] for value in rows.values())


def test_unknown_content_is_not_executed_or_replaced(result):
    assert result['speech']['truth_institutional_teaching_and_endorsement_not_executed']
    assert result['speech']['unknown_relations_refused']
    assert result['reports']['nested_content_not_executed_by_presentation']
    assert result['reports']['unknown_institutional_content_refused']


def test_appointment_can_require_a_voice_that_has_not_been_exercised(result):
    rows=result['appointment']['cases']
    assert len(rows)==32
    for row in rows:
        occurred,delegated,appointed,terms,required=row['states']
        past=occurred and delegated and appointed and terms
        assert row['results']==[past,past and required]
    assert result['appointment']['present_voice_not_required']
    assert result['appointment']['same_closed_voice_target_used']
    assert result['appointment']['standalone_agrees']


def test_source_scope_parent_and_report_are_preserved(result):
    text,_=source_composed();doc=parse(text)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements']==parent['statements']
    assert len(doc['declarations'])==len(parent['declarations'])+7
    assert result['new_primitives']==result['new_author_statements']==0
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result['roundtrips']
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
