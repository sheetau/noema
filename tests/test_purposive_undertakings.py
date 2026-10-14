from copy import deepcopy
import json

import pytest

from noema.grammar import parse
from scripts.check_purposive_undertakings import REPORT,build_report,tier_setup,tier_model,source_setup,source_model,values,guarded,mutual
from scripts.compose_purposive_undertakings import ROOT,PARENT


@pytest.fixture(scope='module')
def result():return build_report()


def test_intended_content_can_be_false_and_true_without_intention(result):
    assert len(result['purposes']['cases'])==4
    for row in result['purposes']['cases']:assert row['results']==[row['aimed'],row['aimed'],row['actual']]
    assert result['purposes']['goal_truth_not_executed']
    assert result['purposes']['unknown_purposes_refused']


def test_purpose_uses_the_same_actor_action_time_and_description(result):
    rows=result['purposes']['contrasts']
    for name in ('person','act','time','alias','separate_witness'):assert rows[name]==[False,False,False]
    assert rows['matching_alternative']==[False,True,False]


def test_purpose_proponents_are_nonempty_selected_parties_not_everyone(result):
    for name in ('empty','outsider','everyone'):assert result['purposes']['contrasts'][name]==[True,False,False]
    assert any(row['aimed'] and row['results'][1] for row in result['purposes']['cases'])


def test_each_subject_has_an_intermediary_without_all_pairs_or_transitivity(result):
    rows=result['tiers']['cases'];assert len(rows)==64
    for row in rows:
        uppera,upperb,aa,ab,ba,bb=row['edges']
        expected=uppera and upperb and (aa or ba) and (ab or bb)
        assert row['results']==[expected,expected]
    assert any(row['edges']==[True,True,True,False,False,True] and row['results']==[True,True] for row in rows)
    assert result['tiers']['contrasts']['direct_only']==[False,False]
    assert result['tiers']['contrasts']['outside_intermediary']==[False,False]


def test_empty_ranges_and_self_supervision_do_not_supply_intermediaries(result):
    for name in ('empty_members','empty_subjects','self_upper'):assert result['tiers']['contrasts'][name]==[False,False]


def test_persistence_covers_the_same_targets_with_changing_delegates(result):
    rows=result['tiers']['contrasts']
    for name in ('future_loss','empty_scope','no_anchor','gap'):assert rows[name]==[True,False]
    assert rows['changing_delegate']==[True,True]
    assert result['tiers']['scopes_fixed_at_anchor']


@pytest.mark.parametrize('name',['jwcontrols','jwmembers','jwsubjects','jwhist','jwrange','jwbefore'])
def test_unknown_tier_relations_are_refused(name):
    text=(ROOT/'examples/v014/purposive-undertakings-core.noema').read_text(encoding='utf-8')
    doc=tier_setup(text);model=tier_model(doc);model[name]=guarded(doc)[name]
    with pytest.raises(ValueError,match='Unrelated primitive'):values(doc,model,mutual.PEOPLE,mutual.SCENES)


def test_source_purpose_achievement_and_invalidity_are_independent(result):
    assert len(result['source']['cases'])==8
    for row in result['source']['cases']:
        assert row['results']==[row['aimed'],not row['aimed'] or row['no_normative_effect'],row['achieved']]
    assert result['source']['goal_binding_contrasts']==['controller','members']
    assert result['source']['global_normative_absence_is_explicit_oracle']
    assert result['source']['closed_goal_roundtrips']


def test_unknown_goal_is_preserved_but_cannot_be_evaluated_as_achieved():
    text=(ROOT/'examples/v014/purposive-undertakings-core.noema').read_text(encoding='utf-8')
    setup=source_setup(text);doc=setup[0];model=source_model(setup);model['dc']=guarded(doc)['dc']
    only=deepcopy(doc);only['statements']=only['statements'][:2]
    assert values(only,model,mutual.PEOPLE,mutual.SCENES)==[True,True]
    with pytest.raises(ValueError,match='Unrelated primitive'):values(doc,model,mutual.PEOPLE,mutual.SCENES)


def test_parent_and_partial_status_are_preserved(result):
    source=parse((ROOT/'examples/v014/kant-purposive-undertakings.noema').read_text(encoding='utf-8'))
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert source['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert len(source['declarations'])==len(parent['declarations'])+7
    assert source['statements']==parent['statements'] and len(source['statements'])==15
    assert result['new_primitives']==result['new_author_statements']==0
    assert result['roundtrips'] and result['purposes']['standalone_agrees'] and result['tiers']['standalone_agrees'] and result['source']['standalone_agrees']
    assert len(result['alignment']['segments'])==2
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
