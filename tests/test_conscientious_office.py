import json

import pytest

from noema.grammar import parse
from scripts.check_conscientious_office import REPORT,build_report
from scripts.compose_conscientious_office import ROOT,PARENT,source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_inability_requires_complete_assessment_of_available_methods(result):
    rows=result['finite']['ability_cases']
    assert len(rows)==64
    for row in rows:
        possible=any(a and s and g for a,s,g in zip(row['available'],row['selected'],row['success']))
        complete=all(not a or s for a,s in zip(row['available'],row['selected']))
        assert row['results']==[possible,complete and not possible,complete]
    assert result['finite']['ability_contrasts']['one_success_one_unassessed']==[True,False,False]
    assert result['finite']['ability_contrasts']['outside_outcomes']==[False,False,False]


def test_office_and_conscience_must_hold_in_the_same_outcome(result):
    assert result['finite']['ability_contrasts']['split_goal']==[False,True,True]
    assert result['finite']['ability_contrasts']['wrong_performer']==[False,True,True]
    assert result['finite']['ability_contrasts']['wrong_office']==[False,True,True]


def test_conditional_consequence_keeps_inability_and_duty_together(result):
    rows=result['finite']['conditional_cases']
    assert len(rows)==64
    for row in rows:
        valid=all(not p or (d and not s) for p,d,s in zip(row['premises'],row['duties'],row['success']))
        assert row['results']==[valid,valid and any(row['premises']),False]
    assert all(row['results']==[all(row['valid'])]*2 for row in result['finite']['incomplete_assessments'])


def test_no_hypotheses_and_no_satisfied_premise_are_different(result):
    rows=result['finite']['case_ranges']
    assert len(rows)==16
    for row in rows:
        if not any(row['selected']):assert row['results']==[False,False]
    row=next(row for row in rows if row['selected']==[True,True] and row['premises']==[False,False])
    assert row['results']==[True,False]


def test_norms_keep_exact_actor_role_activity_description_and_polarity(result):
    rows=result['finite']['binding_contrasts']
    for name in ('source','person','role','activity','description','negative','context'):
        assert rows['norm_'+name]==[False,False]
    assert rows['membership_only_in_case']==[True,False]
    assert all(rows['cases_'+name]==[False,False] for name in ('person','role','document','standard','anchor'))


def test_departure_is_an_agent_bound_future_transition(result):
    rows=result['finite']['departure_cases']
    assert len(rows)==64
    for row in rows:
        expected=row['holding_before'] and not row['holding_after'] and all(row[n] for n in ('change','affected','agent','termination'))
        assert row['results']==[expected,expected]
    assert all(row==[False,False] for row in result['finite']['departure_contrasts'].values())
    assert {'reversed_order','history_missing_start','history_missing_end','termination_role','agent_person'} <= set(result['finite']['departure_contrasts'])


def test_actual_belief_duty_and_departure_do_not_follow_from_hypotheses(result):
    rows=result['finite']['independent_actual_cases']
    assert len(rows)==8
    for row in rows:
        assert row['results']==[row['current_premise'],True,True,row['current_duty'],row['departure']]


def test_normative_reference_does_not_execute_unknown_departure_content(result):
    assert result['finite']['required_target_not_executed']
    assert result['finite']['unknown_inputs_refused']
    assert result['finite']['written_and_constructed_targets_agree']
    assert not result['finite']['conscientiousness_or_normative_validity_proved']


def test_parent_and_roundtrips_preserved_without_promoting_completion(result):
    text,_=source_composed();doc=parse(text)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements']==parent['statements']
    assert len(doc['declarations'])==len(parent['declarations'])+12
    assert result['new_primitives']==result['new_author_statements']==0
    assert result['finite']['standalone_agrees'] and result['roundtrips']
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
