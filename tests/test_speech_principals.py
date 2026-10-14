import json

import pytest

from noema.grammar import parse
from scripts.check_speech_principals import REPORT, build_report
from scripts.compose_speech_principals import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_self_attribution_needs_positive_evidence(result):
    rows = result['finite']['state_cases']
    assert len(rows) == 128
    no_attribution = next(r for r in rows if r['bits'] == [True, False, True, True, False, True, True])
    assert no_attribution['results'][:6] == [False] * 6
    self_only = next(r for r in rows if r['bits'] == [True, False, True, True, True, True, True])
    assert self_only['results'][:6] == [True, False, False, False, True, False]


def test_same_person_can_have_two_differently_attributed_activities(result):
    full = next(r for r in result['finite']['state_cases'] if all(r['bits']))
    assert full['results'] == [True] * 10
    same_activity = result['finite']['binding_contrasts']['same_activity']
    assert same_activity == [True, True, False, True, True, False, True, True, True, True]


def test_public_presentation_does_not_require_reaching_all_readers(result):
    row = next(r for r in result['finite']['reach_cases'] if r['actual'] == [True, False, False] and all(r['intended']))
    assert row['results'] == [True] * 10
    empty = next(r for r in result['finite']['reach_cases'] if not any(r['actual']) and all(r['intended']))
    assert empty['results'] == [False, True, False, True, False, False, True, True, True, False]


def test_intended_readership_is_not_replaced_by_actual_audience(result):
    assert len(result['finite']['reach_cases']) == 64
    row = next(r for r in result['finite']['reach_cases'] if r['actual'] == r['intended'] == [True, False, False])
    assert row['results'] == [True, True, True, True, False, False, True, True, False, True]
    # A narrower intended group still has a public recipient classification in
    # this countermodel; the explicit reader-world equality rejects the link.
    assert result['finite']['binding_contrasts']['outsider'] == [True, True, True, True, False, False, True, True, True, False]


def test_large_office_audience_does_not_create_public_status(result):
    rows = result['finite']['size_cases']
    assert len(rows) == 10
    for row in rows:
        assert row['results'][6] is True
        assert row['results'][7] == row['public_classification']
        assert row['results'][3] == (row['office_size'] > 0)
    large = next(r for r in rows if r['office_size'] == 64 and not r['public_classification'])
    assert large['results'] == [True, True, True, True, False, False, True, False, False, True]


def test_message_force_identity_principal_role_and_context_are_bound(result):
    rows = result['finite']['binding_contrasts']
    assert len(rows) == 73
    for key in ('public_voice_principal', 'public_voice_alias', 'public_voice_force', 'public_delivery_context'):
        assert rows[key][:6] == [False, True, False, True, False, False]
    assert rows['principal_is_self'][:6] == [True, False, False, False, True, False]
    for key in ('channel_alias', 'channel_force', 'channel_channel'):
        assert rows[key][4:6] == [False, False]
        assert rows[key][0] is True


def test_unknown_relations_are_refused_without_executing_norms_or_truth(result):
    assert result['finite']['unknown_relations_refused']
    assert result['finite']['norms_belief_and_message_truth_not_executed']
    assert result['finite']['standalone_agrees']


def test_historical_parent_and_partial_status_are_preserved(result):
    text, _ = source_composed(); doc = parse(text)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['declarations']) == len(parent['declarations']) + 7
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert result['roundtrips']
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
