import json

import pytest

from noema.grammar import parse
from scripts.check_institutional_grounds import REPORT,build_report
from scripts.compose_institutional_grounds import ROOT,PARENT,source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_using_a_reason_does_not_make_it_support_the_judgment(result):
    rows=result['grounds']['cases']
    assert len(rows)==128
    for row in rows:
        used=all(row['states'][:5]);supported=used and all(row['states'][5:])
        assert row['results']==[used,supported,used]
    assert result['grounds']['standalone_agrees']
    assert not result['grounds']['logical_proof_validity_established']


def test_institution_judgment_subject_message_and_context_are_shared(result):
    rows=result['grounds']['binding_contrasts']
    assert len(rows)==19
    for category,fields in (
        ('institution',('principal','judgment','context')),('about',('judgment','subject','context')),
        ('examined',('judgment','subject','context')),('used',('judgment','reason','context'))):
        for field in fields:assert rows[category+'_'+field]==[False]*3
    assert rows['examined_alias']==rows['examined_force']==[False]*3
    for field in ('reason','judgment','context'):assert rows['support_'+field]==[True,False,True]


def test_exhaustiveness_is_local_to_this_judgment_and_context(result):
    rows=result['grounds']['binding_contrasts']
    assert rows['other_judgment_ground']==rows['other_context_ground']==[True]*3
    scopes=result['grounds']['scope_cases']
    assert len(scopes)==8
    assert scopes[0]['results']==[False]*3
    assert scopes[1]['results']==scopes[2]['results']==scopes[5]['results']==[True,True,False]
    assert scopes[4]['results']==[False]*3
    assert scopes[6]['results']==[True,False,True]
    assert scopes[3]['results']==scopes[7]['results']==[True]*3


def test_use_and_complete_listing_can_be_known_without_support(result):
    assert result['grounds']['use_and_exhaustiveness_do_not_require_support']
    assert result['grounds']['unknown_relations_refused']
    assert result['grounds']['human_judgment_and_inner_truth_not_executed']


def test_paired_reports_inner_truth_and_endorsement_vary_independently(result):
    rows=result['reports']['cases']
    assert len(rows)==16
    for row in rows:assert row['results']==[True,True,*row['states'],True]
    assert result['reports']['exact_presented_descriptions_evaluated']
    assert result['reports']['grounds_report_is_assertion']
    assert result['reports']['standalone_agrees']


def test_other_inner_claims_do_not_borrow_the_old_claims_grounds(result):
    rows=result['reports']['inner_description_contrasts']
    assert set(rows)=={'zi','zj'}
    assert all(row==[True,True,True,False,True,True,True] for row in rows.values())


def test_reporting_does_not_execute_unknown_relations_or_create_events(result):
    assert result['reports']['support_not_evaluated_by_reports']
    assert result['reports']['unknown_reported_relations_not_filled']
    assert result['reports']['inner_truth_and_endorsement_may_remain_unknown']
    assert result['reports']['reported_facts_do_not_create_report_acts']


def test_parent_source_scope_and_report_are_preserved(result):
    text,_=source_composed();doc=parse(text)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements']==parent['statements']
    assert len(doc['declarations'])==len(parent['declarations'])+8
    assert result['new_primitives']==result['new_author_statements']==0
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result['roundtrips']
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
