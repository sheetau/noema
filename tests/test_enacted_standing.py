import json

import pytest

from noema.grammar import parse
from scripts.check_enacted_standing import REPORT,build_report
from scripts.compose_enacted_standing import ROOT,PARENT,source_composed


@pytest.fixture(scope='module')
def result():return build_report()


def test_planned_role_actual_execution_and_appointment_are_independent(result):
    rows=result['source']['cases']
    assert len(rows)==128
    for row in rows:
        positioned,executed,entrusted,failed,required,causal,sanction=row['states']
        enacted=positioned and executed
        premise=enacted and failed and required
        assert row['results']==[premise,not premise or causal and sanction,premise,enacted,enacted and not entrusted]
    assert result['source']['standalone_agrees']


def test_appointment_absence_is_not_a_sufficient_or_necessary_evaluative_condition(result):
    rows=result['source']['cases']
    without=next(row for row in rows if row['states']==[True,True,False,False,True,True,True])
    with_failure=next(row for row in rows if row['states']==[True,True,True,True,True,True,True])
    assert without['results']==[False,True,False,True,True]
    assert with_failure['results']==[True,True,True,True,False]


def test_role_and_execution_must_share_person_activity_and_context(result):
    rows=result['source']['contrasts']
    for name in ('position_other_person','position_other_activity','position_other_standing','position_other_context',
                 'execution_other_person','execution_other_activity','execution_other_context'):
        assert rows[name]==[False,True,False,False,False]


def test_appointment_from_another_role_or_context_is_not_imported(result):
    rows=result['source']['contrasts']
    for name in ('appointment_other_person','appointment_other_standing','appointment_other_context','additional_role'):
        assert rows[name]==[True]*5


def test_unknown_appointment_only_blocks_queries_that_need_it(result):
    source=result['source']
    assert source['evaluation_without_appointment_information']
    assert source['unknown_appointment_refused_when_its_absence_is_queried']
    assert set(source['unknown_role_evidence_refused'])=={'cb','cg'}
    assert source['old_assumption_and_quality_callbacks_not_executed']
    assert source['criticism_truth_and_normative_permission_not_executed']


def test_parent_preserved_without_new_primitives_or_author_claims(result):
    text,basis=source_composed();doc=parse(text)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert len(doc['declarations'])-len(parent['declarations'])==7
    assert doc['statements']==parent['statements'] and len(doc['statements'])==15
    assert result['documents'][basis['document']]['primitive_count']==252
    assert result['new_primitives']==result['new_author_statements']==0


def test_actual_enactment_is_not_reported_as_a_proof_of_voluntary_self_adoption(result):
    assert result['alignment']['voluntary_self_adoption_not_claimed']
    assert not result['alignment']['semantic_completion']
    assert result['alignment']['segments'][0]['status']=='partial'
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}


def test_reproducible_report_quotation_and_alphabet_roundtrip(result):
    assert result['source']['role_enactment_can_be_quoted']
    assert result['roundtrips'] and result['parent_preserved']
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
