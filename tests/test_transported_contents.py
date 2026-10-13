import json

import pytest

from noema.grammar import parse
from scripts.check_transported_contents import REPORT, build_report
from scripts.compose_transported_contents import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_membership_retains_identity_and_intermediate_times(result):
    membership = result['membership']
    assert membership['finite_membership_patterns'] == 64
    assert membership['accepted_endpoint_pairs'] == 16
    assert membership['accepted_persistent_sets'] == 4
    assert membership['contrasts']['exit_and_reenter'] == [True, False]
    assert membership['contrasts']['equal_count_replacement'] == [False, False]


def test_period_and_label_scope_are_explicit(result):
    rows = result['membership']['contrasts']
    assert rows['empty_period'] == rows['reference_outside_period'] == [True, False]
    assert rows['outside_label_ignored'] == rows['empty_object_scope'] == [True, True]
    # Deliberately omitting the middle time cannot verify what happened there.
    assert rows['middle_omitted'] == [True, True]


def test_general_persistence_laws_reject_unspecified_time_inference(result):
    laws = result['membership']['laws']
    assert len(laws) == 5
    assert sum(row['status'] == 'valid' for row in laws.values()) == 3
    for name in ('endpoints_alone_imply_persistence', 'persistence_covers_an_unspecified_time'):
        assert laws[name]['status'] == 'invalid'
        assert laws[name]['countermodel_found']


def test_rational_transport_and_flow_do_not_certify_physics(result):
    polynomial = result['polynomial']
    assert len(polynomial['claims']) == 6
    assert sum(row['status'] == 'valid' for row in polynomial['claims'].values()) == 4
    assert polynomial['claims']['balanced_totals_imply_no_exchange_counterexample']['status'] == 'invalid'
    assert polynomial['claims']['fixed_ball_preserves_membership_counterexample']['status'] == 'invalid'
    assert not polynomial['all_real_cut_laws_proved']
    assert not polynomial['electromagnetic_energy_transport_proved']


def test_actual_transported_coordinates_preserve_three_spatial_classes(result):
    rows = result['geometry']['cases']
    assert len(rows) == 36
    assert sum(row['results'][0] for row in rows) == 24
    assert sum(row['results'][1] for row in rows) == 12
    assert all(row['results'][2] for row in rows)
    assert result['geometry']['standalone_agrees']
    assert result['geometry']['real_arithmetic_abstracted_to_registered_rational_cuts']
    assert all(row == [False]*3 for row in result['geometry']['contrasts'].values())


def test_family_uses_same_label_and_spatial_origin_at_each_time(result):
    rows = result['family']['cases']
    assert len(rows) == 9
    assert all(value == [key.startswith('first:')] for key, value in rows.items())
    assert result['family']['origins_time_component_ignored']
    assert result['family']['standalone_agrees']


def test_relative_current_has_correct_direction_and_nonnegative_density(result):
    rows = result['flow']['cases']
    assert len(rows) == 8
    assert sum(value[0] for value in rows.values()) == 3
    assert rows['oblique_flow'] == rows['zero_density'] == [True]
    assert rows['wrong_direction'] == rows['unmatched_transverse_flow'] == rows['negative_density'] == [False]
    assert result['flow']['not_a_boundary_integral_or_continuity_equation']


def test_continuous_time_cannot_be_replaced_with_finite_samples(result):
    assert result['finite_refusal']['refused']
    assert result['finite_refusal']['all_times_not_replaced_with_samples']


def test_source_extension_preserves_parent_and_author_statements(result):
    text, basis = source_composed()
    doc = parse(text)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['declarations']) - len(parent['declarations']) == 16
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert result['documents'][basis['document']]['primitive_count'] == 595


def test_alignment_is_partial_prose_without_inflating_math_coverage(result):
    segments = result['alignment']['segments']
    assert len(segments) == 2
    assert all(row['unit'] == 'einstein-1905:u0205' and row['status'] == 'partial' for row in segments)
    assert all('math_id' not in row for row in segments)
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}


def test_report_is_reproducible_with_formal_and_alphabet_roundtrips(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert result['roundtrips'] and result['parent_preserved']


@pytest.mark.parametrize('labels,bad_label,expected', [
    (('first', 'second'), None, True),
    (('first', 'second'), 'second', False),
    (('first',), 'second', True),
    ((), 'first', True),
])
def test_family_global_condition_requires_each_in_scope_trajectory(labels, bad_label, expected):
    from noema.finite_semantics import FunctionValue
    from scripts.check_comoving_labels import values
    from scripts.check_coordinate_correspondence import abstract
    from scripts.check_described_appraisals import candidate
    from scripts.check_moving_light_trip import literal
    from scripts.check_plane_waveforms import setup, OPS
    from scripts.compose_limits import call as k
    from scripts.compose_transported_contents import POINT, core_composed

    # Abstract ONLY the already separately stated all-real-time property.
    # This tests label/coordinate binding, never proves that property by sampling.
    constants = [k('bb', literal(n)) for n in (5, 1, 0, 0, 5)]
    extra = 'r ja[a] c.r jb[a] ' + POINT + '.q[' + k('segi', 'p ja', 'p jb', *constants) + '].'
    doc = abstract(candidate(core_composed()[0], extra), OPS | {'segg'})
    fixture, model = setup(doc)
    sort = next(d['result'] for d in doc['declarations'] if d['name'] == 'jb')
    origins = {'first': 2, 'second': 3}

    def origin(label):
        return FunctionValue(tuple(sort['parameters']), sort['result'],
            lambda axis: fixture.make(origins.get(label, 0) if axis == 'x' else 0))

    def global_condition(*args):
        numbers = tuple(fixture.read(arg) for arg in args)
        valid = [(5, 1, 0, 0, 5, offset, 0, 0)
                 for label, offset in origins.items() if label != bad_label]
        return numbers in valid

    model.update(ja=lambda label: label in labels, jb=origin, segg=global_condition)
    used = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    assert values(doc, {n: value for n, value in model.items() if n in used},
                  ('x', 'y', 'z', 't', 'first', 'second', 'outside')) == [expected]
