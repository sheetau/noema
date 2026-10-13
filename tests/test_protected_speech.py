import json

import pytest

from noema.grammar import parse
from scripts.check_protected_speech import REPORT, build_report
from scripts.compose_protected_speech import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_protection_does_not_imply_compliance_permission_or_actual_speech(result):
    rows = result['finite']['state_cases']
    assert len(rows) == 32
    for row in rows:
        protected, opposed, banned, allowed, performed = row['states']
        assert row['results'] == [protected, protected and not opposed, protected and banned,
            banned, True, allowed and not banned, True, performed]
    violated = next(row for row in rows if row['states'] == [True, False, True, False, True])
    assert violated['results'] == [True, True, True, True, True, False, True, True]
    no_grant = next(row for row in rows if row['states'] == [True, False, False, False, False])
    assert no_grant['results'] == [True, True, False, False, True, False, True, False]


def test_inner_and_outer_normative_targets_remain_distinct(result):
    rows = result['finite']['binding_contrasts']
    assert len(rows) == 10
    for field in ('outer_source', 'outer_regulator', 'outer_role', 'outer_context'):
        assert rows[field] == [False, False, False, True, True, False, True, False]
    for field in ('inner_regulator', 'inner_person', 'inner_role', 'inner_activity'):
        assert rows[field] == [False, False, False, False, True, False, True, False]
    assert rows['equivalent_alias'] == [False, False, False, True, True, False, True, False]
    assert rows['ban_elsewhere'] == [True, True, False, False, True, False, True, False]


def test_unknown_ban_does_not_prevent_knowing_the_protection_but_blocks_violation(result):
    assert result['finite']['norms_without_fulfillment_assessment']
    assert result['finite']['unknown_norms_and_bans_refused']
    assert result['finite']['violation_without_speech_assessment']


def test_upper_conflict_does_not_erase_the_fact_of_the_negative_demand(result):
    row = next(r for r in result['finite']['state_cases'] if r['states'] == [True, True, True, False, False])
    assert row['results'][:4] == [True, False, True, True]


def test_previous_source_and_author_claims_are_kept(result):
    text, basis = source_composed()
    doc = parse(text)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['statements']) == 15
    audit = result['documents'][basis['document']]
    assert (audit['primitive_count'], audit['definition_count']) == (250, 499)
    assert result['new_primitives'] == result['new_source_assertions'] == 0


def test_report_reproduces_without_certifying_legitimacy_or_semantic_completion(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert result['roundtrips'] and result['parent_preserved']
    assert not result['alignment']['new_source_ranges']
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
