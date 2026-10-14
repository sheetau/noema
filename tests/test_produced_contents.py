import json

import pytest

from noema.grammar import parse
from scripts.check_produced_contents import REPORT,build_report
from scripts.compose_produced_contents import ROOT,PARENT


@pytest.fixture(scope='module')
def result():return build_report()


def test_causal_production_requires_the_joint_act_causal_link_and_result(result):
    rows=result['generic']['cases'];assert len(rows)==32
    for row in rows:assert row['results']==[all(row['bits']),all(row['bits'])]
    assert any(row['bits']==[True,True,True,False,True] and row['results']==[False,False] for row in rows)
    assert any(row['bits']==[True,True,True,True,False] and row['results']==[False,False] for row in rows)


def test_causal_and_actual_result_descriptions_cannot_be_exchanged(result):
    assert result['generic']['contrasts']['alias']==[False,False]
    assert result['generic']['same_description_for_causation_and_result']


def test_shared_actors_and_events_are_not_assembled_from_separate_records(result):
    for name in ('empty_agents','extra_agent','split_act','split_time'):
        assert result['generic']['contrasts'][name]==[False,False]
    assert result['generic']['contrasts']['alternative']==[False,True]
    assert result['generic']['unknown_relations_refused']


def test_purpose_causation_and_retention_are_independent(result):
    rows=result['source']['cases'];assert len(rows)==8
    for row in rows:
        achieved=row['caused'] and row['retained']
        assert row['results']==[row['aimed'],True,achieved,achieved]
    assert result['source']['normative_absence_is_explicit_oracle']


def test_source_uses_people_occurring_acts_and_participation(result):
    assert result['source']['contrasts']=={n:[True,True,False,False] for n in ('nonhuman','no_occurrence','missing_participant')}


def test_known_results_can_be_specialized_and_quoted_without_execution(result):
    assert result['source']['dynamic_and_specialized_agree']
    assert result['source']['closed_goal_roundtrips']
    assert result['source']['unknown_causation_not_inferred']
    for trace in result['source']['specialization']:
        assert trace['bound_positions']==[1]
        assert trace['disquotations_removed']>=1
        assert 'rig' in trace['expanded_definitions']


def test_dynamic_or_unknown_results_cannot_be_silently_quoted(result):
    assert 'disquot' in result['refusals']['dynamic_constructor_unquotable'].lower()
    assert 'Disquotation is not statically' in result['refusals']['unknown_result_not_specialized']


def test_stronger_perpetuation_goals_are_not_finite_successes(result):
    assert result['source']['stronger_goals']=={'hzco':'finite_goal_false','hzcp':'numeric_evaluation_refused'}


def test_parent_and_partial_status_are_preserved(result):
    source=parse((ROOT/'examples/v014/kant-produced-contents.noema').read_text(encoding='utf-8'))
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert source['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert len(source['declarations'])==len(parent['declarations'])+3
    assert source['statements']==parent['statements'] and len(source['statements'])==15
    assert result['new_primitives']==result['new_author_statements']==0
    assert result['roundtrips'] and result['generic']['standalone_agrees'] and result['source']['standalone_agrees']
    assert result['alignment']['segments'][0]['text']=='zu verewigen'
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
