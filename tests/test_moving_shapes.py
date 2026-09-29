from pathlib import Path

import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import encode, decode
from scripts.compose_moving_shapes import composed
from scripts.check_moving_shapes import numerical_checks, observation_checks, proof_checks, source_alignment, arithmetic_document, claim_document, CLAIMS


def test_surface_time_slice_and_axes_are_distinct():
    cases = numerical_checks()
    assert len(cases) == 16
    assert cases['longitudinal_surface_at_lab_time_zero']['actual']
    assert cases['transverse_surface_at_lab_time_zero']['actual']
    assert not cases['contracting_transverse_axis_is_wrong']['actual']
    assert cases['moving_center_at_later_time']['actual']
    assert not cases['earlier_slice_not_reused_at_later_time']['actual']
    assert cases['generic_slice_captures_time_two']['actual']
    assert not cases['diameters_are_not_semiaxes']['actual']
    assert not cases['zero_axis_at_light_speed_is_not_a_regular_sphere']['actual']
    assert 'refused' in cases['all_times_and_positions_not_finitely_sampled']


def test_observation_membership_and_geometry_must_agree_in_one_frame():
    cases = observation_checks()
    assert len(cases) == 10
    assert cases['lab_slice']['actual']
    assert all(not row['actual'] for label, row in cases.items() if label != 'lab_slice')
    assert cases['wrong_geometric_radius']['membership_and_simultaneity']
    assert not cases['same_event_twice']['membership_and_simultaneity']


def test_polynomial_derivations_keep_the_domain_and_simultaneity_conditions():
    pytest.importorskip('z3')
    results = proof_checks()
    assert len(results) == 17
    assert sum(r['status'] == 'valid' for r in results.values()) == 14
    assert sum(r['status'] == 'invalid' for r in results.values()) == 3
    assert results['surface_equivalence_under_unit_phi_transform']['status'] == 'valid'
    assert results['simultaneous_in_both_frames_requires_zero_speed_or_equal_x']['status'] == 'valid'
    assert {d['name'] for d in arithmetic_document()['declarations'] if d['kind'] == 'primitive'} == {'aa', 'ab', 'ac', 'ad'}
    text = claim_document()
    assert CLAIMS.read_text(encoding='utf-8') == text
    doc = parse(text)
    assert len(doc['statements']) == 14
    assert all(s['kind'] == 'assert' for s in doc['statements'])
    assert parse(format_graph(doc)) == parse(decode(encode(format_graph(doc), 'v2'))) == doc


def test_sources_and_real_cut_forms_are_partial_and_roundtrip():
    text, basis = composed()
    doc = parse(text)
    audit = audit_basis(doc, basis)
    assert (audit['primitive_count'], audit['definition_count']) == (10, 81)
    assert not audit['semantic_equivalence_to_source_proven']
    for notation in ('full', 'compact'):
        canonical = format_graph(doc, notation)
        assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
    assert '<svg' in render(text, alphabet='v2')
    if Path('artifacts/written-units-v1/einstein-1905.json').exists():
        alignment = source_alignment()
        assert len(alignment['selections']) == 3
        assert all(s['status'] == 'partial' for s in alignment['selections'])
        assert alignment['same_time_bound_to_frame']
