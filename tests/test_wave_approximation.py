import json

import pytest

from noema.grammar import parse
from scripts.check_wave_approximation import REPORT, build_report
from scripts.compose_wave_approximation import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_component_bounds_and_exact_zero_are_proved_with_negative_controls(result):
    rows=result['polynomial']['claims']
    assert len(rows)==9
    rejected={'same_bound_not_preserved_by_mixing','missing_other_field_error_is_not_safe','negative_bound_is_not_an_error_budget'}
    assert all(row['status']==('invalid' if name in rejected else 'valid') for name,row in rows.items())
    assert not result['polynomial']['global_real_field_transport_proved']


def test_two_field_error_budgets_are_transformed_with_coordinates_and_components(result):
    rows=result['points']['cases']
    assert len(rows)==60
    assert all(row[:2]==[True,True] for row in rows.values())
    assert any(not row[2] for row in rows.values())
    assert result['points']['cumulative_and_standalone_agree']


def test_closed_boundary_and_zero_tolerance_do_not_become_approximate_equality(result):
    assert result['scalars']=={'exact':[True],'positive_boundary':[True],'negative_boundary':[True],
        'beyond_bound':[False],'negative_bound':[False],'zero_bound_nonzero_error':[False]}


def test_mathematical_boundedness_and_contextual_sufficiency_are_separate(result):
    rows=result['sufficiency']['cases']
    assert len(rows)==15
    assert rows['baseline']==rows['zero_error_exact']==[True]
    for name in ('loose_but_not_sufficient','not_sufficient','wrong_purpose','missing_global_bound'):
        assert rows[name]==[False]


def test_region_origin_time_and_fixed_bound_are_not_satisfied_at_one_selected_point(result):
    rows=result['sufficiency']['cases']
    for name in ('empty_region','origin_excluded','origin_wrong_time','error_at_second_point',
                 'too_small_bound','negative_bound','zero_bound_nonzero_error'):
        assert rows[name]==[False]


def test_transport_is_a_guarded_conditional_not_an_assertion_of_its_premise(result):
    assert len(result['transport_condition']['cases'])==8
    assert result['transport_condition']['light_speed_boundary_rejected']
    assert result['transport_condition']['false_premise_is_not_evidence_of_an_approximation']


def test_finite_fixture_does_not_establish_global_bound_or_sine(result):
    checks=result['sufficiency']
    assert checks['global_bound_and_harmonic_conditions_are_fixture_oracles']
    assert checks['nonharmonic_profile_only_tests_argument_wiring']
    assert 'Cannot finitely quantify' in checks['global_bound_refused_without_oracle']


def test_existing_exact_reading_definitions_and_author_claims_are_preserved(result):
    doc=parse(source_composed()[0]);parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements']==parent['statements']
    assert len(doc['declarations'])-len(parent['declarations'])==11
    assert result['new_primitives']==result['new_author_statements']==0
    assert result['sizes']['einstein-wave-approximation']['statements']==173


def test_source_alignment_retains_choice_of_error_criterion_and_incomplete_semantics(result):
    assert result['alignment']['chosen_operational_realization_not_unique_source_definition']
    assert result['alignment']['segments'][0]['unit']=='einstein-1905:u0179'
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
