from pathlib import Path

import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import encode, decode
from scripts.compose_coordinates import composed
from scripts.check_coordinates import numerical_checks, observation_checks, proof_checks


def test_unknown_phi_and_all_origins_are_preserved():
    cases = numerical_checks()
    assert len(cases) == 9
    assert cases['phi_two_is_not_replaced_by_one']['actual']
    assert not cases['phi_two_cannot_leave_transverse_axes_unchanged']['actual']
    assert cases['velocity_function_and_four_independent_origins']['actual']
    assert cases['zero_phi_can_satisfy_raw_equations']['actual']
    assert not cases['zero_phi_is_not_a_coordinate_map']['actual']


def test_event_frame_context_unit_and_calibration_links():
    cases = observation_checks()
    assert len(cases) == 15
    assert cases['baseline']['actual']
    assert all(not r['actual'] for name, r in cases.items() if name != 'baseline')


def test_interval_and_inverse_are_universal_polynomial_identities():
    pytest.importorskip('z3')
    results = proof_checks()
    assert len(results) == 2
    assert all(r['status'] == 'valid' for r in results.values())


def test_source_alignment_and_meaning_inventory():
    text, basis = composed()
    doc = parse(text)
    audit = audit_basis(doc, basis)
    assert audit['primitive_count'] == 10
    assert audit['definition_count'] == 50
    assert set(audit['definition_dependencies']['definition_primitive_dependencies']['eg']) == {
        'aa', 'ab', 'ac', 'ad', 'pa', 'pb', 'pc', 'pd', 'pe', 'pf'}
    assert not audit['semantic_equivalence_to_source_proven']
    for notation in ('compact', 'full'):
        canonical = format_graph(doc, notation)
        assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
    assert '<svg' in render(text, alphabet='v2')


def test_original_four_equations_are_tracked_as_partial():
    pytest.importorskip('z3')
    if not Path('artifacts/written-units-v1/einstein-1905.json').exists():
        pytest.skip('Source artifact is prepared separately')
    from scripts.check_coordinates import build_report
    report = build_report()
    assert report['source_alignment']['selections'][0]['math_id'] == 'M0135'
    assert all(s['status'] == 'partial' for s in report['source_alignment']['selections'])
    assert report['verified_full_units'] == 0
    assert not report['general_real_coordinate_laws_machine_verified']
