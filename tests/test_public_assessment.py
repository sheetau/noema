import json

import pytest

from noema.grammar import parse
from scripts.check_public_assessment import REPORT, build_report
from scripts.compose_public_assessment import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_criteria_are_composed_and_message_force_is_preserved(result):
    rows = result['finite']['cases']
    assert len(rows) == 24
    for row in rows:
        expected = any(not row['satisfied'][('zc', 'zd').index(name)] for name in row['criteria'])
        assert row['results'] == [expected, True]
    for state in ([False, False], [False, True], [True, False], [True, True]):
        selected = [r for r in rows if r['satisfied'] == state]
        assert selected[0]['results'] == [False, True]
        assert selected[3]['results'] == selected[4]['results'] == selected[5]['results']
    assert result['finite']['unknown_criterion_refused']


def test_purpose_judgment_deficiency_and_publication_are_independent(result):
    rows = result['source']['cases']
    assert len(rows) == 16
    assert all(row['states'] == row['results'] for row in rows)
    false_claim_judged = next(r for r in rows if r['states'] == [True, True, False, True])
    assert false_claim_judged['results'] == [True, True, False, True]


def test_intended_goal_and_actual_judgment_keep_their_own_bindings(result):
    rows = result['source']['contrasts']
    assert len(rows) == 9
    for name, observed in rows.items():
        assert observed == ([False, True, False, False] if name.startswith('purpose_') else [True, False, False, False])


def test_intention_is_not_filled_in_from_achievement_and_does_not_require_truth(result):
    assert result['source']['purpose_without_execution_receipt_judgment_or_truth']
    assert result['source']['unknown_intention_and_judgment_refused']


def test_parent_claims_and_meaning_inventory_are_preserved(result):
    text, basis = source_composed()
    doc = parse(text)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['statements']) == 15
    audit = result['documents'][basis['document']]
    assert (audit['primitive_count'], audit['definition_count']) == (252, 505)
    assert result['documents']['examples/v014/criterion-failures.noema']['primitive_count'] == 0
    assert result['new_primitives'] == 2
    assert result['new_source_assertions'] == 0


def test_saved_report_reproduces_and_does_not_certify_criterion_adequacy(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert result['roundtrips'] and result['parent_preserved']
    assert not result['alignment']['semantic_completion']
    assert not result['alignment']['new_source_ranges']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
