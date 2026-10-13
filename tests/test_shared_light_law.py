import json

import pytest

from noema.grammar import parse
from scripts.check_shared_light_law import REPORT, build_report
from scripts.compose_shared_light_law import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_units_are_converted_independently_before_comparing_factors(result):
    rows = result['bindings']['cases']
    assert len(rows) == 24
    assert {row['speed'] for row in rows} == {-3, 0, 3}
    assert {tuple(row['scales']) for row in rows} == {(1, 1, 1, 1), (2, 3, 5, 7)}
    assert all(row['results'] == [True, True, True] for row in rows)
    assert result['bindings']['contrasts']['scale_without_value_conversion'] == [False, False, False]


def test_matching_numbers_cannot_replace_matching_referents(result):
    rows = result['bindings']['contrasts']
    for index in range(4):
        for field in ('target', 'kind', 'frame', 'event', 'unit', 'context', 'owner', 'unit_kind'):
            assert rows[f'record_{index}_wrong_{field}'] == [False, True, False]
    for name in ('same_frame', 'same_kind', 'wrong_observer', 'wrong_context', 'wrong_target',
                 'frames_swapped', 'wrong_rest_frame', 'wrong_motion'):
        assert rows[name] == [False, True, False]


def test_records_may_hold_even_when_the_transformation_is_false(result):
    rows = result['bindings']['contrasts']
    for name in ('energy_uses_squared_factor', 'rate_unchanged', 'same_ratio_wrong_motion_factor'):
        assert rows[name] == [True, False, False]


def test_equal_factors_do_not_assert_equal_quantities_or_a_universal_constant(result):
    assert result['bindings']['contrasts']['different_energy_to_frequency_ratio'] == [True]*3
    assert not result['bindings']['energy_equals_frequency_required']
    assert not result['bindings']['universal_energy_frequency_constant_asserted']


def test_ratios_require_positive_values_and_unit_scales(result):
    rows = result['bindings']['contrasts']
    for name in ('zero_energy_ratio_undefined', 'negative_rates', 'zero_frequency'):
        assert rows[name] == [True, False, False]
    for name in ('zero_scale', 'negative_scale'):
        assert rows[name] == [False]*3
    assert result['bindings']['missing_reading_refused']


def test_the_new_definitions_reuse_the_existing_language_and_keep_parent(result):
    text, _ = source_composed()
    doc = parse(text); parent = parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['declarations']) == len(parent['declarations'])+3
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert result['bindings']['standalone_agrees']


def test_source_alignment_remains_partial(result):
    span = result['alignment']['segments'][0]
    assert span['unit'] == 'einstein-1905:u0214' and span['status'] == 'partial'
    assert 'Bewegungszustande des Beobachters' in span['text']
    assert not result['alignment']['semantic_completion']
    assert not result['bindings']['universal_physical_law_proved']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}


def test_reproducible_report_and_both_notations(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert result['roundtrips'] and result['parent_preserved']
