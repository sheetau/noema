import json

import pytest

from noema.grammar import parse
from scripts.check_area_time_flux import REPORT,build_report
from scripts.compose_area_time_flux import ROOT,PARENT,source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_total_and_normalized_balance_are_equivalent_for_positive_extent(result):
    claims=result['polynomial']['claims']
    assert len(claims)==9
    for name in ('common_area_time_preserves_total_balance','positive_area_time_recovers_rate_balance',
                 'positive_area_time_makes_rates_unique','zero_area_is_not_a_normalization',
                 'zero_duration_is_not_a_normalization','nonunit_area_and_time_are_allowed','negative_work_is_allowed'):
        assert claims[name]['status']=='valid'
    for name in ('total_energy_equals_its_normalized_rate','area_alone_is_sufficient'):
        assert claims[name]['status']=='invalid'


def test_positive_extents_independent_units_and_signed_work(result):
    rows=result['binding']['cases']
    assert len(rows)==36
    assert {row['speed'] for row in rows}=={-3,0,3}
    assert {row['amplitude'] for row in rows}=={0,2}
    assert {tuple(row['scales']) for row in rows}=={(1,1,1,1,1),(2,3,5,7,11)}
    assert all(row['results']==[True]*5 for row in rows)
    assert result['binding']['standalone_agrees']


def test_each_record_retains_its_target_kind_frame_event_unit_context_and_owner(result):
    contrasts=result['binding']['contrasts']
    for row in range(5):
        for label in ('target','kind','frame','event','unit','context','owner','unit_kind'):
            assert contrasts['record_'+str(row)+'_wrong_'+label]==[False,True,True,False,True]
    for name in ('episode','mirror','patch','interval','incominglight','outgoinglight','frame','observer','context'):
        assert contrasts['wrong_'+name]==[False,True,True,False,True]


def test_nonuniform_or_incompatible_quantity_setup_is_not_guessed(result):
    contrasts=result['binding']['contrasts']
    for name in ('areakind_confused_with_energy','timekind_confused_with_energy','wrong_rest_frame','nonuniform_exchange'):
        assert contrasts[name]==[False,True,True,False,True]
    assert result['binding']['unknown_readings_and_exchange_refused']


def test_zero_or_negative_extent_and_unconverted_units_are_rejected(result):
    contrasts=result['binding']['contrasts']
    for field in ('areavalue','durationvalue'):
        for value in (0,-1):
            assert contrasts[field+'_'+str(value)]==[True,False,False,False,True]
    for name in ('scale_changed_without_conversion','zero_unit_scale','negative_unit_scale'):
        assert contrasts[name]==[False,False,False,False,True]


def test_amounts_cannot_be_replaced_by_rates_or_have_work_sign_reversed(result):
    contrasts=result['binding']['contrasts']
    for name in ('total_energy_replaced_by_rate','time_factor_omitted','work_sign_reversed'):
        assert contrasts[name]==[True,False,False,False,False]
    assert contrasts['wrong_reflection_amplitude']==[True,True,False,False,True]
    assert contrasts['missing_pi_condition']==[True,True,True,False,True]


def test_area_time_normalization_does_not_determine_stationary_pressure(result):
    for value in (1,99):
        assert result['binding']['contrasts']['stationary_pressure_'+str(value)]==[True]*5
    assert not result['binding']['stationary_pressure_determined']
    assert not result['polynomial']['physical_energy_principle_proved']
    assert not result['polynomial']['all_real_cut_laws_proved']


def test_parent_scope_and_report_are_preserved(result):
    text,_=source_composed();doc=parse(text)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements']==parent['statements']
    assert len(doc['declarations'])==len(parent['declarations'])+9
    assert result['new_primitives']==result['new_author_statements']==0
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result['roundtrips']
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
