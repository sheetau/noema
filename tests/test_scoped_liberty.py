import json

import pytest

from noema.grammar import parse
from scripts.check_scoped_liberty import REPORT, build_report
from scripts.compose_scoped_liberty import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_empty_scope_does_not_create_a_witness_or_a_prohibition(result):
    rows=result['generic']['selection_cases']
    assert len(rows)==64
    for row in rows:
        if not any(row['selected']):assert row['results']==[True,False,False,False,False,False]


def test_absent_permission_is_not_an_explicit_ban(result):
    rows=result['generic']['norm_cases'];assert len(rows)==256
    row=next(r for r in rows if r['states']==[[False]*4,[False]*4])
    assert row['results']==[False,False,False,False,True,False]
    restricted=next(r for r in rows if r['states']==[[False,True,False,False],[False,False,True,False]])
    assert restricted['results']==[False,False,True,False,False,False]


def test_permission_to_perform_does_not_imply_permission_to_refrain(result):
    rows=result['generic']['norm_cases']
    row=next(r for r in rows if r['states']==[[False,False,True,False]]*2)
    assert row['results']==[True,True,False,False,False,False]
    choice=next(r for r in rows if r['states']==[[False,False,True,True]]*2)
    assert choice['results']==[True,True,False,False,False,True]


def test_conflicting_policies_are_not_mislabeled_as_clean_bans(result):
    rows=result['generic']['norm_cases']
    row=next(r for r in rows if r['states']==[[False,True,True,False],[False,False,True,False]])
    assert row['results']==[False,False,False,True,False,False]
    # Positive performance permission alone does not rule out a separate
    # clash between a performance duty and permission to refrain.
    other=next(r for r in rows if r['states']==[[True,False,True,True],[False,False,True,False]])
    assert other['results']==[True,True,False,True,False,False]


def test_each_activity_keeps_its_own_description_and_norm_source(result):
    rows=result['generic']['binding_contrasts']
    assert len(rows)==7
    for key in ('norm_source','norm_person','norm_role','norm_context','norm_alias','swapped_targets'):
        assert rows[key]==[False,False,False,False,True,False]


def test_outer_requirement_does_not_assert_actual_restriction(result):
    rows=result['source']['state_cases'];assert len(rows)==16
    for row in rows:
        assert row['results'][4]==row['outer']
        assert row['results'][1]==(row['private_banned'] and not row['private_allowed'])
    unimplemented=next(r for r in rows if r['private_allowed'] and not r['private_banned'] and r['public_allowed'] and r['outer'])
    assert unimplemented['results']==[True,False,True,False,True,True]
    no_norms=next(r for r in rows if not r['private_allowed'] and not r['private_banned'] and r['public_allowed'] and r['outer'])
    assert no_norms['results']==[False,False,True,False,True,False]


def test_inner_and_outer_bindings_polarity_and_arity_remain_distinct(result):
    rows=result['source']['binding_contrasts'];assert len(rows)==19
    for name in ('outer_source','outer_person','outer_role','outer_context','outer_alias','outer_reordered','outer_extra','outer_missing','outer_positive'):
        assert rows[name]==[True,False,True,False,False,True]
    for row in result['source']['length_cases']:
        assert row['results'][-1]==(len(row['bindings'])==3)
        assert row['results'][4] is True


def test_unknown_relations_do_not_turn_into_absent_norms_or_actual_execution(result):
    assert result['generic']['unknown_scope_norms_and_targets_refused']
    assert result['generic']['actual_target_truth_not_executed']
    assert result['source']['unknown_relations_refused']
    assert result['source']['outer_norm_does_not_evaluate_inner_policy']
    assert result['source']['execution_not_used_to_select_scope']


def test_parent_roundtrips_and_interpretive_limits_are_retained(result):
    doc=parse(source_composed()[0]);parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements']==parent['statements']
    assert len(doc['declarations'])==len(parent['declarations'])+13
    assert result['new_primitives']==result['new_author_statements']==0
    assert result['generic']['standalone_agrees'] and result['source']['standalone_agrees']
    assert result['roundtrips']
    assert {s['status'] for s in result['alignment']['segments']}=={'explicit_interpretive_annotation'}
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
