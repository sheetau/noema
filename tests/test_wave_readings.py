import json

import pytest

from noema.grammar import parse
from scripts.check_wave_readings import REPORT, build_report
from scripts.compose_wave_readings import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_both_field_kinds_accept_the_same_wave_in_two_frames_and_different_units(result):
    rows=result['bindings']['cases']
    assert len(rows)==68
    assert rows['electric:baseline']==rows['magnetic:baseline']==[True]
    assert all(row==[name.endswith(':baseline')] for name,row in rows.items())
    assert result['bindings']['cumulative_and_standalone_agree']


def test_record_observer_target_frame_event_and_context_are_not_interchangeable(result):
    rows=result['bindings']['cases']
    for side in ('electric','magnetic'):
        for mismatch in ('wrong_record_wave','wrong_wave_assignment','wrong_record_observer','wrong_record_frame',
                'wrong_record_event','wrong_coordinate_event','wrong_record_id','wrong_context','wrong_record_context',
                'observer_in_wrong_frame','not_an_observer'):
            assert rows[side+':'+mismatch]==[False]


def test_units_are_tied_to_quantity_kind_and_positive_scale(result):
    rows=result['bindings']['cases']
    for side in ('electric','magnetic'):
        for mismatch in ('same_number_different_unit','wrong_record_kind','wrong_unit_kind','wrong_unit_scale',
                'wrong_record_unit','zero_unit_scale','negative_unit_scale','negative_amplitude'):
            assert rows[side+':'+mismatch]==[False]


def test_wave_parameters_fields_region_and_frame_motion_remain_bound(result):
    rows=result['bindings']['cases']
    for side in ('electric','magnetic'):
        for mismatch in ('wrong_frequency','wrong_direction','wrong_transverse_amplitude','wrong_speed',
                'wrong_motion_binding','wrong_new_field','wrong_new_region','missing_frame_field_assignment'):
            assert rows[side+':'+mismatch]==[False]


def test_all_real_conditions_are_oracles_only_in_the_wiring_fixture(result):
    assert result['bindings']['global_conditions_are_explicit_fixture_oracles']
    assert result['bindings']['nonharmonic_profile_used_only_to_test_argument_wiring']
    assert result['bindings']['finite_samples_do_not_prove_full_field_equality']
    assert not result['bindings']['physical_measurement_occurrence_verified']
    assert set(result['global_refusals'])=={'sdv2','sai2','saj2'}
    assert all('Cannot finitely quantify' in message for message in result['global_refusals'].values())


def test_parent_and_all_existing_author_statements_are_preserved(result):
    doc=parse(source_composed()[0]);parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements']==parent['statements']
    assert len(doc['declarations'])-len(parent['declarations'])==4
    assert result['new_primitives']==result['new_author_statements']==0
    assert result['sizes']['einstein-wave-readings']['statements']==173


def test_measurement_clause_is_partial_without_claiming_light_source_or_prose_completion(result):
    rows=result['alignment']['segments']
    assert len(rows)==1 and rows[0]['unit']=='einstein-1905:u0197'
    assert rows[0]['end']-rows[0]['start']==len(rows[0]['source'])
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
