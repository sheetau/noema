from pathlib import Path

import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.compose_clock_protocol import compose, composed_basis
from scripts.check_clock_protocol import physical_checks, coordinate_checks


def test_clocks_events_places_frames_units_and_missing_readings_are_distinguished():
    cases = physical_checks()
    assert len(cases) == 14
    assert cases['correct_bindings']['actual'] is True
    assert all(not case['actual'] for name, case in cases.items() if name != 'correct_bindings')


def test_coordinate_changes_preserve_sync_only_under_the_stated_conditions():
    pytest.importorskip('z3')
    cases = coordinate_checks()
    assert len(cases) == 10
    assert cases['shifting_only_reflection_clock_preserves_sync']['status'] == 'invalid'
    assert all(case['status'] == 'valid' for name, case in cases.items()
               if name != 'shifting_only_reflection_clock_preserves_sync')


def test_combined_protocol_retains_declared_meanings_and_both_layers_without_models():
    doc = parse(compose())
    stored = parse(Path('examples/v011/einstein-clock-protocol.noema').read_text(encoding='utf-8'))
    assert stored == doc
    audit = audit_basis(doc, composed_basis())
    assert audit['primitive_count'] == 13 and audit['definition_count'] == 13
    assert set(audit['definition_dependencies']['definition_primitive_dependencies']['db']) == {
        'aa', 'ab', 'ac', 'ca', 'cb', 'cc', 'cd', 'ce', 'cf', 'cg', 'ch', 'ci'}
    for notation in ('full', 'compact'):
        text = format_graph(doc, notation)
        assert parse(text) == doc
        assert parse(decode(encode(text, 'v2'))) == doc
