import json

import pytest

from noema.grammar import parse
from scripts.check_energy_questions import REPORT, build_report
from scripts.compose_energy_questions import ROOT, PARENT, REFERENCES, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_question_preserves_frame_direction_and_unit_scaling(result):
    rows = result['questions']['cases']
    assert len(rows) == 18
    assert {row['speed'] for row in rows} == {-3, 0, 3}
    assert {row['scale'] for row in rows} == {1, 2}
    assert all(row['results'] == [True, True] for row in rows)
    assert result['questions']['standalone_agrees']


def test_same_value_does_not_authorize_swapping_referents(result):
    rows = result['questions']['contrasts']
    for name in ('wrong_target', 'frames_swapped', 'same_frame', 'wrong_kind', 'wrong_unit',
                 'wrong_physical_context', 'unassigned_complex', 'wrong_region', 'wrong_motion'):
        assert rows[name] == [False, True]


def test_numeric_and_global_premises_are_not_silently_filled_in(result):
    rows = result['questions']['contrasts']
    for name in ('wrong_value', 'wrong_amplitude', 'wrong_volume', 'missing_pi_premise', 'missing_volume_premise'):
        assert rows[name] == [False, True]
    assert result['questions']['pi_3_is_only_an_abstract_binding_token']
    assert result['questions']['global_pi_and_volume_conditions_abstracted']
    assert result['questions']['region_fingerprints_are_not_global_proofs']


def test_zero_energy_is_allowed_but_negative_values_and_scales_are_rejected(result):
    rows = result['questions']['contrasts']
    assert rows['zero_amplitude_zero_energy'] == [True, True]
    for name in ('negative_energy', 'zero_scale', 'negative_scale'):
        assert rows[name] == [False, True]


def test_presented_question_is_independent_of_its_candidate_truth(result):
    rows = result['questions']['contrasts']
    assert rows['wrong_value'] == [False, True]
    assert rows['no_attribution'] == [True, False]
    assert rows['neither_candidate_nor_attribution'] == [False, False]
    for name in ('wrong_author', 'wrong_scope', 'wrong_text_context', 'wrong_question_description'):
        assert rows[name] == [True, False]
    assert len(rows) == 24


def test_quotation_does_not_execute_or_require_physical_inputs(result):
    assert result['quotation']['uninterpreted_physical_inputs_not_executed']
    assert result['quotation']['quoted_question'] == {'kind': 'call', 'symbol': 'sehd', 'arguments': []}
    assert result['finite_refusal']['refused']
    assert result['finite_refusal']['no_finite_answer_search_claim']


def test_one_question_attribution_is_added_without_an_energy_answer_assertion(result):
    text, basis = source_composed()
    doc = parse(text); parent = parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'][:-1] == parent['statements']
    assert len(doc['statements']) == 174
    assert doc['statements'][-1]['body']['symbol'] == 'zih'
    declarations = {d['name']: d for d in doc['declarations']}
    assert declarations['sehc']['result']['kind'] == declarations['sehd']['result']['kind'] == 'question'
    assert all(declarations[symbol]['parameters'] == [] for symbol in REFERENCES.values())
    assert result['new_local_references'] == 20
    assert result['new_logical_or_grammatical_primitives'] == result['new_author_assertions_of_energy_value'] == 0
    assert result['documents'][basis['document']]['primitive_count'] == 615


def test_new_source_spans_preserve_partial_status(result):
    segments = result['alignment']['segments']
    assert len(segments) == 2
    assert all(s['unit'] == 'einstein-1905:u0205' and s['status'] == 'partial' for s in segments)
    assert '[M0356]' in segments[0]['text'] and '[M0357]' in segments[1]['text']
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}


def test_report_and_notation_are_reproducible(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert result['roundtrips'] and result['parent_preserved']
