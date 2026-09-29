from pathlib import Path

import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import encode, decode
from scripts.compose_moving_clocks import composed, ALIASES
from scripts.check_moving_clocks import numerical_checks, observation_checks, proof_checks, source_alignment, claim_document, CLAIMS


def test_rate_reading_elapsed_and_remainder_are_separate():
    cases = numerical_checks()
    assert len(cases) == 16
    assert cases['three_fifths_speed_four_fifths_rate']['actual']
    assert not cases['beta_is_not_rate']['actual']
    assert cases['past_origin_readings_are_allowed']['actual']
    assert not cases['zero_interval_cannot_measure_a_rate']['actual']
    assert cases['duration_ten_lost_two_approx_one_point_eight']['actual']
    assert not cases['zero_error_is_wrong_at_nonzero_speed']['actual']
    assert cases['arbitrary_common_dial_origin']['actual']
    assert cases['explicit_dial_scale']['actual']


def test_the_same_clock_events_units_worldline_and_calibration_are_required():
    cases = observation_checks()
    assert len(cases) == 18
    assert cases['baseline']['actual'] and cases['scaled_dial']['actual']
    assert all(not row['actual'] for label, row in cases.items() if label not in ('baseline', 'scaled_dial'))


def test_noema_claims_prove_the_remainder_without_a_series_shortcut():
    pytest.importorskip('z3')
    results = proof_checks()
    assert len(results) == 22
    assert sum(row['status'] == 'valid' for row in results.values()) == 17
    assert sum(row['status'] == 'invalid' for row in results.values()) == 5
    assert results['exact_remainder_identity']['status'] == 'valid'
    assert results['fourth_order_remainder_bounds']['status'] == 'valid'
    assert results['common_calibration_origin_cancels_in_elapsed_reading']['status'] == 'valid'
    text = claim_document()
    assert CLAIMS.read_text(encoding='utf-8') == text
    doc = parse(text)
    assert len(doc['statements']) == 17
    assert all(s['kind'] == 'assert' for s in doc['statements'])
    assert parse(decode(encode(format_graph(doc), 'v2'))) == doc


def test_clock_primitives_are_reused_and_real_cut_forms_roundtrip():
    text, basis = composed()
    doc = parse(text)
    audit = audit_basis(doc, basis)
    assert (audit['primitive_count'], audit['definition_count']) == (15, 95)
    assert not audit['semantic_equivalence_to_source_proven']
    for original, current in ALIASES.items():
        record = next(r for r in basis['primitives'] if r['symbol'] == current)
        assert record['source_convention'] == 'clock-physical-basis-v1:' + original
    for notation in ('compact', 'full'):
        canonical = format_graph(doc, notation)
        assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
    assert '<svg' in render(text, alphabet='v2')
    if Path('artifacts/written-units-v1/einstein-1905.json').exists():
        alignment = source_alignment()
        assert len(alignment['selections']) == 5
        assert all(s['status'] == 'partial' for s in alignment['selections'])
        assert not alignment['accelerated_or_closed_paths_covered']
