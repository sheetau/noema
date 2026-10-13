import json

import pytest

from noema.grammar import parse
from scripts.check_mirror_reflection import REPORT, build_report
from scripts.compose_mirror_reflection import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_three_stages_imply_the_derived_result(result):
    claims = result['polynomial']['claims']
    assert claims['three_stages_imply_closed_form']['status'] == 'valid'
    assert claims['boost_factor_positive']['status'] == 'valid'
    assert claims['mirror_rest_reflection_is_involutive']['status'] == 'valid'
    assert claims['closed_form_uses_same_amplitude_frequency_factor']['status'] == 'valid'
    assert len(result['numeric']['cases']) == 30
    assert all(row['results'][:2] == [True, True] for row in result['numeric']['cases'])


def test_printed_inconsistency_is_retained_and_not_called_a_transcription_error(result):
    discrepancy = result['facsimile']['discrepancy']
    assert discrepancy['snapshot_denominator'] == discrepancy['facsimile_denominator'] == '(1-v/V)^2'
    assert discrepancy['staged_derivation_denominator'] == '1-(v/V)^2'
    assert not discrepancy['is_transcription_correction']
    assert not result['facsimile']['snapshot_modified']
    claims = result['polynomial']['claims']
    assert claims['printed_formula_matches_moving_example']['status'] == 'invalid'
    assert claims['derived_formula_matches_moving_example']['status'] == 'valid'
    assert claims['printed_frequency_agrees_only_at_zero_speed']['status'] == 'valid'
    for row in result['numeric']['cases']:
        assert row['results'][2] == (row['speed'] == 0)
    assert result['numeric']['contrasts']['printed_value_breaks_the_staged_result'] == [False, False, True]


def test_intermediate_values_cannot_be_taken_from_another_stage(result):
    rows = result['numeric']['contrasts']
    for role in ('first_amplitude', 'first_direction', 'first_frequency',
                 'reflected_amplitude', 'reflected_direction', 'reflected_frequency'):
        assert rows['wrong_'+role] == [False, True, False]
    for role in ('final_amplitude', 'final_direction', 'final_frequency'):
        assert rows['wrong_'+role] == [False, False, False]
    assert rows['omit_direction_reversal'] == [False, True, False]
    assert rows['returning_to_old_frame_does_not_undo_reflection'] == [False, False, False]


def test_zero_amplitude_is_allowed_but_negative_amplitude_and_nonpositive_frequency_are_not(result):
    assert sum(row['amplitude'] == 0 for row in result['numeric']['cases']) == 15
    for name in ('negative_amplitude', 'zero_frequency', 'negative_frequency'):
        assert result['numeric']['contrasts'][name] == [False, False, False]


def test_moving_plane_becomes_the_zero_coordinate_plane(result):
    rows = result['plane']['cases']
    assert len(rows) == 27
    assert all(row['results'] == [row['x'] == 0, row['x'] == 0, row['x'] == row['speed']*row['time']] for row in rows)
    assert any(row['results'][0] != row['results'][2] for row in rows)
    assert not result['plane']['mirror_material_properties_included']


def test_source_math_alignment_keeps_partial_status(result):
    rows = result['alignment']['segments']
    assert {row['math_id'] for row in rows} == {'M0368', 'M0372', 'M0374', 'M0376'}
    assert all(row['status'] == 'partial' for row in rows)
    assert not result['alignment']['semantic_completion']
    assert result['alignment']['printed_and_derived_frequency_not_identified']
    assert not result['polynomial']['all_real_cut_field_laws_proved']
    assert not result['numeric']['physical_incidence_and_measurement_relations_verified']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}


def test_parent_and_grammar_are_preserved(result):
    text, _ = source_composed()
    doc = parse(text); parent = parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['declarations']) == len(parent['declarations'])+15
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert result['numeric']['standalone_agrees']


def test_report_and_notation_are_reproducible(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert result['roundtrips'] and result['parent_preserved']
