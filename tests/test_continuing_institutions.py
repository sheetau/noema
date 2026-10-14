from copy import deepcopy
import json

import pytest

from noema.grammar import parse
from scripts.check_continuing_institutions import REPORT,build_report,setup,model_for,source_setup,source_model,values,guarded,old
from scripts.compose_continuing_institutions import ROOT,PARENT


@pytest.fixture(scope='module')
def result():return build_report()


def test_point_tail_and_endpoint_free_history_are_distinct(result):
    rows=result['finite']['cases'];assert len(rows)==16
    for row in rows:assert row['results']==[row['edges'][0] and row['edges'][1],all(row['edges']),False]
    assert result['finite']['no_finite_history_claimed_endless']


def test_members_and_subjects_can_turn_over_without_losing_the_institution(result):
    for name in ('stable','member_turnover','target_turnover','turnover'):
        assert result['finite']['contrasts'][name]==[True,True,False]
    assert result['source']['comparisons']['stable']==[True,True]
    assert result['source']['comparisons']['turnover']==[False,True]


def test_selected_period_is_not_substituted_for_whole_future(result):
    assert result['finite']['contrasts']['short_scope']==[True,False,False]
    assert result['finite']['contrasts']['empty_scope']==[True,True,False]
    assert result['source']['comparisons']['short_scope']==[True,False]
    assert result['source']['comparisons']['empty_scope']==[False,True]


def test_empty_populations_or_invalid_history_do_not_supply_continuity(result):
    rows=result['finite']['contrasts']
    for name in ('empty_current_members','empty_current_subjects'):assert rows[name]==[False,False,False]
    for name in ('empty_future_members','empty_future_subjects','future_loss','missing_anchor','cycle'):assert rows[name]==[True,False,False]


def test_general_temporal_laws_and_counterexamples_are_not_finite_sampling(result):
    claims=result['laws']['claims']
    assert set(claims)=={'endless_implies_future_tail','future_tail_includes_current_roles','a_last_point_blocks_endlessness',
        'point_implies_whole_future','whole_future_implies_endlessness','whole_future_requires_original_people'}
    for name in ('endless_implies_future_tail','future_tail_includes_current_roles','a_last_point_blocks_endlessness'):
        assert claims[name]['status']=='valid' and not claims[name]['countermodel_found']
    for name in ('point_implies_whole_future','whole_future_implies_endlessness','whole_future_requires_original_people'):
        assert claims[name]['status']=='invalid' and claims[name]['countermodel_found']
    assert 'arbitrary nonempty' in result['laws']['domain']


def test_endpoint_free_and_unbounded_numeric_time_have_different_witnesses(result):
    witnesses=result['numeric_witnesses']
    assert all(row['status']=='valid' for row in witnesses['claims'].values())
    assert witnesses['situations_not_retyped_as_numbers']
    assert result['horizon_refusal']['refused']
    assert 'rational number domain' in result['horizon_refusal']['reason']


def test_unending_and_numeric_goals_are_representable_without_success(result):
    rows=result['source']['cases'];assert len(rows)==12
    assert {r['target'] for r in rows}=={'hzcn','hzco','hzcp'}
    for row in rows:assert row['results']==[row['aimed'],not row['aimed'] or row['no_normative_effect']]
    assert result['source']['numeric_goal_can_be_quoted_without_evaluation']
    assert result['source']['numeric_evaluation_refused']
    assert result['source']['normative_absence_is_explicit_oracle']


@pytest.mark.parametrize('name',['jwmembers','jwsubjects','jwcontrols','jwhist','jwbefore'])
def test_unknown_population_or_history_is_not_completed(name):
    text=(ROOT/'examples/v014/continuing-institutions-core.noema').read_text(encoding='utf-8')
    doc=setup(text);model=model_for(doc);model[name]=guarded(doc)[name]
    with pytest.raises(ValueError,match='Unrelated primitive'):values(doc,model,old.mutual.PEOPLE,old.mutual.SCENES)


def test_unknown_infinite_goal_does_not_block_intention_but_blocks_evaluation():
    text=(ROOT/'examples/v014/continuing-institutions-core.noema').read_text(encoding='utf-8')
    s=source_setup(text,'hzco');doc=s[0];model=source_model(s);model['dc']=guarded(doc)['dc']
    only=deepcopy(doc);only['statements']=only['statements'][:2]
    assert values(only,model,old.mutual.PEOPLE,old.mutual.SCENES)==[True,True]
    with pytest.raises(ValueError,match='Unrelated primitive'):values(doc,model,old.mutual.PEOPLE,old.mutual.SCENES)


def test_parent_and_partial_status_are_preserved(result):
    source=parse((ROOT/'examples/v014/kant-continuing-institutions.noema').read_text(encoding='utf-8'))
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert source['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert len(source['declarations'])==len(parent['declarations'])+7
    assert source['statements']==parent['statements'] and len(source['statements'])==15
    assert result['new_primitives']==result['new_author_statements']==0
    assert result['roundtrips'] and result['finite']['standalone_agrees'] and result['source']['standalone_agrees']
    assert result['source']['closed_goal_roundtrips']
    assert result['alignment']['segments'][0]['text']=='unaufhörliche'
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
