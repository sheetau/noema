import json

import pytest

from noema.grammar import parse
from scripts.check_provisional_order import REPORT, build_report, source_setup, source_model, values, office, SCENES
from scripts.compose_provisional_order import ROOT, PARENT


@pytest.fixture(scope='module')
def result(): return build_report()


def test_first_milestone_strong_weak_and_inclusive_maintenance(result):
    assert len(result['temporal']['cases']) == 64
    for row in result['temporal']['cases']:
        maintained, stops = row['bits'][:3], row['bits'][3:]
        first = next((i for i, stop in enumerate(stops) if stop), None)
        strong = first is not None and all(maintained[:first])
        assert row['results'] == [strong and first == 2, strong,
            strong or first is None and all(maintained), strong and maintained[first]]


def test_history_scope_and_order_are_not_optional(result):
    for name in ('foreign_start', 'missing_start', 'cyclic', 'missing_order'):
        assert result['temporal']['contrasts'][name] == [False] * 4
    assert result['temporal']['contrasts']['foreign_end'] == [False, True, True, True]
    assert result['temporal']['contrasts']['foreign_milestone'] == [False, False, True, False]


def test_order_and_each_citizens_permission_must_hold_together(result):
    assert len(result['source']['cases']) == 16
    for row in result['source']['cases']:
        active, first, second, reached = row['bits']; state = active and first and second
        assert row['results'] == [state, state and reached, state, state and reached]
    for name in ('missing_second_permission', 'missing_second_activity', 'other_regime', 'foreign_permission', 'opposed_permission'):
        assert result['source']['contrasts'][name] == [False] * 4


def test_midperiod_gap_cannot_be_hidden_by_success_at_endpoints(result):
    for name in ('permission_gap', 'order_gap'):
        assert result['source']['contrasts'][name] == [True, False, False, False]


def test_milestone_does_not_force_abolition_and_boundary_is_explicit(result):
    for name in ('boundary_permission', 'boundary_order'):
        assert result['source']['contrasts'][name] == [True, True, True, False]
    assert result['source']['initial_milestone'] == [False, True, True, False]
    assert result['temporal']['later_failure_not_forced']


def test_new_citizens_are_checked_at_their_own_points():
    doc = source_setup((ROOT / 'examples/v014/provisional-order-core.noema').read_text(encoding='utf-8'))
    model = source_model(doc, (True, True, False, True))
    model['jycitizens'] = lambda population, person, point: population == 'issuer' and (
        person == 'person' or person == 'other' and point in ('middle', 'end'))
    assert values(doc, model, office.DOMAIN, SCENES) == [True, False, False, False]
    model['jycitizens'] = lambda population, person, point: population == 'issuer' and (
        person == 'person' or person == 'other' and point == 'end')
    assert values(doc, model, office.DOMAIN, SCENES) == [True, True, True, False]


def test_unknown_is_not_false_and_permission_does_not_execute_speech(result):
    assert result['temporal']['unknown_conditions_refused']
    assert result['source']['unknown_relations_refused']
    assert result['source']['actual_speech_and_criticism_truth_not_executed']


def test_parent_and_partial_interpretation_status_are_preserved(result):
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-provisional-order.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 9
    assert child['statements'] == parent['statements'] and len(child['statements']) == 15
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
