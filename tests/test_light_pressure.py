import json

import pytest

from noema.grammar import parse
from scripts.check_light_pressure import REPORT, build_report
from scripts.compose_light_pressure import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_pressure_follows_from_reflection_and_work_at_nonzero_speed(result):
    claims = result['polynomial']['claims']
    for name in ('reflection_agrees_with_preceding_closed_form', 'incoming_side_implies_outgoing_side',
                 'flux_difference_identity', 'nonzero_velocity_work_determines_pressure'):
        assert claims[name]['status'] == 'valid'
    assert len(result['numeric']['cases']) == 30
    assert all(row['results'][1:] == [True, True] for row in result['numeric']['cases'])


def test_zero_speed_does_not_determine_pressure_from_work(result):
    claims = result['polynomial']['claims']
    assert claims['zero_velocity_allows_two_different_pressures']['status'] == 'valid'
    assert claims['work_alone_fixes_stationary_pressure']['status'] == 'invalid'
    rows = result['numeric']['contrasts']
    assert rows['stationary_alternate_pressure'] == [True, False, True]
    assert rows['stationary_nonzero_work'] == [False, True, True]
    assert rows['stationary_negative_pressure'] == [False, False, True]
    assert not result['polynomial']['stationary_pressure_from_work_alone']


def test_approaching_mirror_retains_negative_work(result):
    rows = result['numeric']['cases']
    assert any(row['speed'] < 0 and row['work'].startswith('-') and row['results'][0] for row in rows)
    assert result['numeric']['contrasts']['approaching_mirror_work_sign_reversed'] == [False, True, True]


def test_incidence_side_is_checked_even_for_zero_amplitude(result):
    rows = result['numeric']['cases']
    assert sum(row['results'][0] for row in rows) == 18
    assert result['numeric']['contrasts']['nonnegative_fluxes_on_wrong_side_still_rejected'] == [False, True, True]
    assert any(row['incoming'] == row['outgoing'] == row['pressure'] == '0' and row['results'][0] for row in rows)


def test_leading_term_has_an_error_bound_and_is_not_the_exact_moving_value(result):
    claims = result['polynomial']['claims']
    for name in ('leading_term_matches_closed_form_at_rest', 'exact_error_identity', 'leading_error_bound_for_half_light_speed'):
        assert claims[name]['status'] == 'valid'
    assert claims['leading_term_is_exact_at_nonzero_speed']['status'] == 'invalid'
    assert result['numeric']['contrasts']['use_leading_term_as_exact_pressure'] == [False, False, True]
    assert result['numeric']['contrasts']['wrong_leading_term'] == [True, True, False]


def test_domain_and_pi_conditions_are_explicit(result):
    rows = result['numeric']['contrasts']
    for name in ('unknown_pi', 'wrong_pi_token', 'zero_pi', 'negative_amplitude', 'invalid_direction_cosine'):
        assert rows[name] == [False]*3
    for name in ('zero_light_speed', 'negative_light_speed', 'speed_at_light_speed', 'speed_beyond_negative_light_speed'):
        assert rows[name] == [False, False, True]
    assert result['numeric']['pi_3_is_only_an_abstract_binding_token']
    assert result['numeric']['pi_integral_condition_abstracted']


def test_shared_fluxes_and_work_cannot_be_replaced_independently(result):
    rows = result['numeric']['contrasts']
    for role in ('finalamplitude', 'finalax', 'incoming', 'outgoing', 'work'):
        assert rows['wrong_'+role] == [False, True, True]
    assert rows['wrong_pressure'] == [False, False, True]
    assert len(rows) == 22


def test_source_alignment_and_physical_limits_remain_explicit(result):
    assert {row['math_id'] for row in result['alignment']['segments']} == {'M0377', 'M0378', 'M0379', 'M0380', 'M0381', 'M0382'}
    assert not result['alignment']['semantic_completion']
    assert not result['polynomial']['all_real_cut_field_laws_proved']
    assert not result['polynomial']['real_continuity_and_momentum_transfer_proved']
    assert not result['numeric']['measurement_units_and_physical_energy_principle_proved']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}


def test_parent_and_grammar_are_preserved(result):
    text, _ = source_composed()
    doc = parse(text); parent = parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['declarations']) == len(parent['declarations'])+17
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert result['numeric']['standalone_agrees']


def test_report_and_notation_are_reproducible(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert result['roundtrips'] and result['parent_preserved']
