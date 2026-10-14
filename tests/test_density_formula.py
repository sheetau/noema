"""An isolated source relation must not inherit a stronger physical theory."""
from copy import deepcopy
import json

import pytest

from noema.grammar import parse
from scripts.check_density_formula import REPORT, REVIEW, build_report, review_packet
from scripts.compose_density_formula import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


@pytest.fixture(scope='module')
def review():
    return json.loads(REVIEW.read_text(encoding='utf-8')), parse(source_composed()[0])


def test_fraction_form_is_equivalent_on_its_defined_domain(result):
    claims = result['polynomial']['claims']
    assert {name: row['status'] for name, row in claims.items()} == {
        'five_fraction_relations_iff_isolated_formula': 'valid',
        'negative_nonzero_denominator_is_not_omitted': 'valid',
        'formula_imposes_subluminal_material_speed': 'invalid',
        'formula_requires_positive_density': 'invalid',
    }
    assert not result['polynomial']['empirical_electrodynamics_proved']


def test_formula_does_not_add_density_sign_or_material_speed_bounds(result):
    cases = result['finite']['cases']
    assert len(cases) == 27
    assert all(row['results'] == [True] * 4 for row in cases)
    assert {row['density'] for row in cases} == {-4, 0, 4}
    assert any(row['speed'] == 3 and row['velocity'] == [10, 0, 0] for row in cases)


def test_only_three_diagonal_derivatives_enter_the_formula(result):
    rows = result['finite']['contrasts']
    assert len(rows) == 32
    for i in range(3):
        for j in range(4):
            assert rows[f'jet_{i}_{j}'] == ([False, False, True, False] if i == j else [True] * 4)
    assert rows['field_offdiagonal'] == [True] * 4
    assert result['finite']['exactly_three_new_diagonal_partials']
    assert result['finite']['old_field_magnetic_and_other_derivatives_not_executed']


def test_equal_trace_does_not_replace_actual_derivatives_at_the_same_point(result):
    rows = result['finite']['contrasts']
    for variant in ('compensated_diagonals', 'field_diagonal', 'wrong_point',
                    'outside_region', 'missing_x', 'missing_y', 'missing_z'):
        assert rows[variant] == [True, False, True, True]
    assert result['finite']['unknown_inputs_refused']


def test_undefined_fraction_is_rejected_even_when_the_trace_agrees(result):
    assert result['finite']['contrasts']['zero_denominator'] == [False, False, False, True]


@pytest.mark.parametrize('mutation', ['relation', 'parameter', 'output', 'input', 'excluded', 'closed', 'truth', 'completion'])
def test_review_rejects_missing_correspondence_and_unsupported_completion(review, mutation):
    original, doc = review
    packet = deepcopy(original)
    if mutation == 'relation':
        packet['source_relations'].pop()
    elif mutation == 'parameter':
        packet['parameter_bindings'][1]['index'] = 0
    elif mutation == 'output':
        packet['source_relations'][4]['output_parameter'] = 3
    elif mutation == 'input':
        packet['source_relations'][4]['input_parameters'] = [0, 1, 2, 7, 4]
    elif mutation == 'excluded':
        packet['checks'][5]['status'] = 'not_a_translation_gate'
    elif mutation == 'closed':
        packet['checks'][5]['status'] = 'checked'
    elif mutation == 'truth':
        packet['checks'][8]['status'] = 'checked'
    else:
        packet['semantic_completion'] = True
    with pytest.raises(ValueError):
        review_packet(packet, doc)


def test_source_truth_and_translation_obligations_are_distinct(result):
    review = result['unit_review']
    assert review['open'] == ['source_context_bindings', 'discourse_role',
                              'concept_grounding', 'whole_unit_decision']
    assert review['source_truth_is_not_a_translation_gate']
    assert review['decision'] == 'partial'
    assert not review['semantic_completion']
    assert not result['finite']['full_source_context_or_author_introduction_completed']


def test_parent_source_range_roundtrips_and_report_are_retained(result, review):
    _, doc = review
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['statements']) == 174
    assert len(doc['declarations']) == len(parent['declarations']) + 3
    assert result['new_primitives'] == result['new_author_statements'] == 0
    segment = result['alignment']['segments'][0]
    assert (segment['unit'], segment['math_id']) == ('einstein-1905:u0236', 'M0390')
    assert result['finite']['standalone_agrees'] and result['roundtrips']
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
