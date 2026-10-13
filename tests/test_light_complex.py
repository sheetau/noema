import json

import pytest

from noema.grammar import parse
from scripts.check_light_complex import REPORT, build_report
from scripts.compose_light_complex import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_polynomial_derivations_do_not_certify_spatial_measure(result):
    rows = result['polynomial']['claims']
    assert len(rows) == 10
    assert sum(row['status'] == 'valid' for row in rows.values()) == 7
    assert all(rows[name]['status'] == 'invalid' for name in (
        'unchanged_volume_counterexample', 'square_energy_factor_counterexample', 'negative_beta_counterexample'))
    assert not result['polynomial']['volume_measure_law_proved']
    assert not result['polynomial']['all_real_cut_laws_proved']


def test_original_surface_transformed_slice_and_explicit_ellipsoid_agree(result):
    rows = result['geometry']['cases']
    assert len(rows) == 75
    assert all(row['results'][:3] == [row['results'][0]]*3 for row in rows)
    assert sum(row['results'][0] for row in rows) == 45
    assert sum(row['results'][3] for row in rows) == 60
    assert any(row['results'][0] != row['wrong_old_zero_time_surface'] for row in rows)
    assert result['geometry']['standalone_agrees']


def test_invalid_shape_domains_do_not_acquire_a_slice(result):
    rows = result['geometry']['contrasts']
    assert set(rows) == {'zero_radius','negative_radius','nonunit_direction','zero_light','light_speed','superluminal'}
    assert all(row == [False,False] for row in rows.values())


def test_common_density_conversion_and_volume_give_energy_factor(result):
    rows = result['energy']['cases']
    assert len(rows) == 30
    assert all(row['results'] == [True]*3 for row in rows)
    assert {row['conversion'] for row in rows} == {1,8}
    assert result['energy']['common_conversion_is_parameter_not_pi_definition']
    assert result['energy']['standalone_agrees']


def test_energy_frequency_power_and_volume_cannot_be_interchanged(result):
    rows = result['energy']['contrasts']
    assert len(rows) == 13
    assert rows['unchanged_volume'] == rows['changed_conversion'] == rows['wrong_squared_amplitude'] == [False,True,True]
    assert rows['wrong_frequency'] == [True,True,False]
    assert rows['squared_energy_factor'] == [False]*3
    assert rows['zero_energy'] == rows['negative_energy'] == [False]*3
    assert rows['zero_power'] == rows['zero_volume'] == [False,True,True]
    assert rows['light_speed'] == rows['superluminal'] == [False]*3


def test_parallel_root_has_positive_branch_and_full_cut_quantification_refuses(result):
    assert len(result['parallel']) == 6
    assert sum(row[0] for row in result['parallel'].values()) == 3
    assert result['finite_refusal']['refused']


def test_facsimile_is_pinned_without_claiming_whole_page_verification(result):
    review = result['facsimile']
    assert [row['printed_page'] for row in review['images']] == [913,914]
    assert review['reviewed_math_ids'] == ['M0355','M0359','M0362','M0365','M0367']
    assert not review['snapshot_modified']
    assert not review['whole_page_semantics_verified']
    assert all(len(value)==64 for value in review['snapshot_math_sha256'].values())


def test_parent_and_existing_assertions_remain_unchanged(result):
    text,basis = source_composed()
    doc,parent = parse(text),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert result['sizes']['einstein-light-complex'] == {'characters':268860,'statements':173}
    assert result['sizes']['light-complex-core'] == {'characters':8429,'statements':0}
    assert result['documents'][basis['document']]['primitive_count'] == 595
    assert result['new_primitives'] == result['new_author_statements'] == 0


def test_reproducible_report_keeps_partial_source_status(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert len(result['alignment']['segments']) == 6
    assert all(row['status'] == 'partial' for row in result['alignment']['segments'])
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784':0,'einstein-1905':0}
    assert result['roundtrips'] and result['parent_preserved']
