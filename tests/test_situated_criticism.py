import json

import pytest

from noema.grammar import parse
from scripts.check_situated_criticism import REPORT,build_report
from scripts.compose_situated_criticism import ROOT,PARENT,source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_whole_conditional_separates_antecedent_consequence_and_witness(result):
    rows=result['source']['cases']
    assert len(rows)==64
    for row in rows:
        required,spoken,linked,quality,causal,sanction=row['states']
        base=required and spoken and linked
        premise=base and quality
        consequence=causal and sanction
        assert row['results']==[base,premise,consequence,not premise or consequence,premise]
    assert result['source']['standalone_agrees']


def test_topic_correspondence_keeps_every_required_remittance_argument(result):
    rows=result['source']['contrasts']
    for field in ('subject','issuer','person','role','action','description','context'):
        assert rows['charge_'+field]==[False,False,True,True,False]
    assert result['source']['unknown_topic_correspondence_refused']


def test_communication_uses_one_act_speaker_topic_message_and_nonempty_audience(result):
    rows=result['source']['contrasts']
    for name in ('empty_audience','wrong_speaker','wrong_topic','wrong_message','split_speech','speech_context'):
        assert rows[name]==[False,False,True,True,False]


def test_causal_and_punitive_consequences_refer_to_the_antecedents_speech(result):
    rows=result['source']['contrasts']
    for name in ('causal_other_action','sanction_other_person','sanction_other_offense'):
        assert rows[name]==[True,True,False,False,True]
    assert rows['quality_of_other_action']==[True,False,True,True,False]
    assert result['source']['independent_causal_and_sanction_outcomes']


def test_scope_is_not_a_single_favorable_case_or_an_assumed_instance(result):
    rows=result['source']['contrasts']
    assert rows['empty_cases']==[True,True,True,False,False]
    assert rows['inapplicable_cases']==[True,True,True,True,False]
    assert rows['mixed_cases']==[True,True,True,False,True]


def test_payment_and_criticism_content_are_composed_but_not_asserted_true(result):
    assert result['source']['actual_payment_message_truth_permission_and_public_role_not_executed']
    assert result['source']['payment_description']['symbol']=='hzah'
    assert result['source']['criticism_description']['symbol']=='rfd'


def test_no_new_primitives_and_no_new_author_assertions(result):
    text,basis=source_composed();doc=parse(text)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert len(doc['declarations'])-len(parent['declarations'])==7
    assert doc['statements']==parent['statements'] and len(doc['statements'])==15
    assert result['documents'][basis['document']]['primitive_count']==252
    assert result['new_primitives']==result['new_author_statements']==0


def test_partial_interpretation_and_reproducible_evidence(result):
    assert result['alignment']['conditional_scope_is_explicit_interpretation']
    assert result['alignment']['segments'][0]['status']=='partial'
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result['roundtrips'] and result['parent_preserved']
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
