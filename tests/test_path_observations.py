import pytest

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_path_observations import CLAIMS, claim_document, observation_checks, proof_checks, source_alignment
from scripts.compose_path_observations import ROOT, composed


def test_shared_events_readings_and_coordinate_units_are_required():
    cases = observation_checks()
    assert len(cases) == 35
    assert sum(row['actual'] for row in cases.values()) == 7
    assert cases['common_dial_scale']['actual']
    assert cases['arbitrary_time_origin']['actual']
    assert cases['two_spatial_components']['actual']
    assert cases['open_path']['actual']
    assert not cases['open_path_not_closed']['actual']
    assert not cases['equal_coordinates_different_event']['actual']
    assert not cases['shared_event_reading_reset']['actual']
    assert not cases['reference_not_initially_synchronous']['actual']
    assert not cases['reference_resets_at_arrival']['actual']
    assert not cases['arrival_at_other_place']['actual']


def test_telescoping_step_and_comparison_follow_from_explicit_premises():
    pytest.importorskip('z3')
    results = proof_checks()
    assert len(results) == 4
    assert all(row['status'] == 'valid' for row in results.values())
    assert CLAIMS.read_text(encoding='utf-8') == claim_document()
    doc = parse(claim_document())
    assert len(doc['statements']) == 4
    assert parse(decode(encode(format_graph(doc), 'v2'))) == doc


def test_observation_library_keeps_original_physical_basis():
    text, basis = composed()
    doc = parse(text)
    audit = audit_basis(doc, basis)
    assert (audit['primitive_count'], audit['definition_count']) == (15, 107)
    assert not audit['semantic_equivalence_to_source_proven']
    assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    for notation in ('compact', 'full'):
        canonical = format_graph(doc, notation)
        assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
    assert '<svg' in render(text, alphabet='v2')


def test_source_map_does_not_claim_curve_or_distant_clock_completion():
    alignment = source_alignment()
    assert len(alignment['selections']) == 3
    assert all(row['status'] == 'partial' for row in alignment['selections'])
    assert alignment['selections'][0]['definitions'] == ['ja', 'jb']
    assert alignment['selections'][-1]['definitions'] == ['jc', 'jd']
    assert 'distant-clock synchronization in u0126' in alignment['uncovered']
    assert 'continuous-curve limit' in alignment['uncovered']
