import json

import pytest

from noema.grammar import parse
from scripts.check_plane_waveforms import REPORT, build_report
from scripts.compose_plane_waveforms import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_profile_factorization_uses_polynomial_identity_and_a_counterexample(result):
    claims=result['polynomial']['claims']
    assert claims['s6b_commutes_with_shared_profile']['status']=='valid'
    assert claims['s6c_commutes_with_shared_profile']['status']=='valid'
    assert claims['different_profiles_are_not_interchangeable']['status']=='invalid'
    assert not result['polynomial']['real_cut_field_laws_proved']


def test_all_six_components_agree_for_shared_profiles_in_two_coordinate_systems(result):
    rows=result['waveforms']['cases']
    assert len(rows)==44
    assert all(row==[True]*12 for name,row in rows.items() if name.startswith('valid_'))
    assert result['waveforms']['cumulative_and_standalone_agree']
    assert result['waveforms']['profiles_are_exact_rational_functions_not_claimed_sine']


def test_phase_inverse_map_and_component_signs_have_distinguishing_cases(result):
    rows=result['waveforms']['cases']
    wrong=[row for name,row in rows.items() if not name.startswith('valid_')]
    assert len(wrong)==8
    assert all(row[:6]==[True]*6 and not all(row[6:]) for row in wrong)


def test_oscillator_initial_values_and_derivatives_remain_separate_conditions(result):
    rows=result['harmonic']['cases']
    assert rows['correct_initial_jet']==[True,True]
    assert rows['linear_pair_fails_away_from_origin']==[True,False]
    assert rows['scaled_jet_wrong_normalization']==[False,True]
    assert rows['wrong_sine_slope']==rows['wrong_cosine_slope']==[True,False]
    assert rows['wrong_cosine_sign']==rows['shifted_profile_wrong_origin']==[False,False]


def test_all_real_oscillator_and_raw_derivative_cannot_be_certified_by_finite_sampling(result):
    assert set(result['harmonic']['refusals'])=={'global','raw_derivative'}
    assert not result['harmonic']['sine_existence_and_uniqueness_proved']
    assert not result['waveforms']['general_real_function_identity_proved']


def test_wave_domain_requires_light_speed_frequency_and_unit_direction(result):
    assert len(result['domains'])==8
    assert result['domains']['valid']==[True]
    assert all(row==[False] for name,row in result['domains'].items() if name!='valid')


def test_every_amplitude_is_bound_to_same_transform_including_longitudinal_ones(result):
    assert len(result['amplitudes'])==21
    assert all(row==[name.endswith(':-1')] for name,row in result['amplitudes'].items())


def test_existing_author_statements_are_preserved_and_no_new_primitive_is_used(result):
    text,_=source_composed();doc=parse(text)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements']==parent['statements']
    assert len(doc['declarations'])-len(parent['declarations'])==10
    assert result['new_primitives']==result['new_author_statements']==0
    assert result['sizes']['einstein-plane-waveforms']['statements']==173


def test_associations_are_partial_and_amplitude_norm_ratio_is_not_silently_corrected(result):
    assert {row['math_id'] for row in result['alignment']['segments']}=={'M0320','M0325'}
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
