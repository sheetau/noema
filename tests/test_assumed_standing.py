import json

import pytest

from noema.grammar import parse
from scripts.check_assumed_standing import REPORT,build_report
from scripts.compose_assumed_standing import ROOT,PARENT,source_composed


@pytest.fixture(scope='module')
def result():return build_report()


def test_claiming_a_standing_and_failing_its_conditions_are_both_required(result):
    rows=result['source']['cases']
    assert len(rows)==64
    for row in rows:
        assumes,first,second,required,causal,sanction=row['states']
        premise=required and assumes and not(first and second)
        assert row['results']==[premise,not premise or causal and sanction,premise]
    assert result['source']['standalone_agrees']


def test_actor_activity_standing_context_and_criterion_subjects_stay_bound(result):
    assert len(result['source']['binding_contrasts'])==7
    assert all(row==[False,True,False] for row in result['source']['binding_contrasts'].values())


def test_missing_or_unknown_criteria_are_not_evidence_of_failure(result):
    rows=result['source']['list_contrasts']
    assert rows['empty']==rows['fulfilled_only']==[False,True,False]
    assert rows['duplicate_failure']==rows['reordered']==[True,True,True]
    assert result['source']['unknown_criterion_refused']


def test_composed_property_replaces_the_opaque_quality_callback(result):
    assert result['source']['opaque_quality_parameter_not_executed']
    assert result['source']['permission_and_message_truth_not_executed']
    assert result['source']['composed_property_can_be_quoted']


def test_historical_evidence_is_design_evidence_not_runtime_translation(result):
    evidence=result['lexical_evidence']
    assert evidence['sources']==3
    assert evidence['historical_usage_supports_a_candidate_not_unique_interpretation']
    assert evidence['online_sources_not_consulted_by_noema_parser_or_interpreter']
    assert evidence['checks_are_offline_metadata_integrity_not_new_web_verification']


def test_no_new_primitives_or_author_assertions(result):
    text,basis=source_composed();doc=parse(text)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert len(doc['declarations'])-len(parent['declarations'])==6
    assert doc['statements']==parent['statements'] and len(doc['statements'])==15
    assert result['documents'][basis['document']]['primitive_count']==252
    assert result['new_primitives']==result['new_author_statements']==0


def test_candidate_reading_does_not_claim_equivalence_or_completion(result):
    assert result['alignment']['segments'][0]['status']=='partial'
    assert not result['alignment']['lexical_equivalence_certified']
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}


def test_reproducible_report_and_roundtrips(result):
    assert result['parent_preserved'] and result['roundtrips']
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
