import json

import pytest

from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_capacity_changes import REPORT, build_report
from scripts.compose_capacity_changes import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_each_assessed_person_has_exactly_one_endpoint_class(result):
    rows = result['finite']['individual_cases']
    assert len(rows) == 32
    for row in rows:
        assert sum(row['results']) == int(all(row['assessed']) and row['ordered'])


def test_net_zero_does_not_erase_a_gain_and_a_loss(result):
    rows = result['finite']['cohort_cases']
    assert len(rows) == 16
    swapped = next(row for row in rows if row['states'] == [[False, True], [True, False]])
    unchanged = next(row for row in rows if row['states'] == [[True, True], [False, False]])
    assert swapped['counts'] == [1, 1, 0, 0]
    assert unchanged['counts'] == [0, 0, 1, 1]
    assert swapped['results'] == unchanged['results'] == [True, True]


def test_endpoint_retention_and_absence_do_not_claim_whole_interval_persistence(result):
    assert result['finite']['intermediate_changes'] == {
        'temporary_loss': [False, False, True, False], 'temporary_gain': [False, False, False, True]}
    row = result['source']['cases']['intermediate_gain_lost']
    assert row['counts'] == [0, 0, 0, 2]
    assert row['results'] == [True, True, False, True]


def test_complete_cohort_assessment_is_not_inferred_from_raw_counts(result):
    rows = result['finite']['contrasts']
    assert rows['reordered']['results'] == [True, True]
    for name in ('duplicate', 'missing', 'empty', 'unassessed', 'reverse'):
        assert rows[name]['results'] == [False, True]
    for name in ('unassessed_before', 'unassessed_after'):
        assert result['source']['cases'][name]['results'] == [False, True, False, False]


def test_gains_do_not_infer_an_actual_self_achievement_process(result):
    rows = result['source']['cases']
    assert len(rows) == 16
    for name in ('no_causal_result', 'wrong_result_description', 'other_person_changed',
            'other_agent', 'no_self_work', 'no_change', 'future_achievement'):
        assert rows[name]['counts'] == [1, 0, 0, 1]
        assert rows[name]['results'] == [True, True, False, False]
    assert rows['later_loss']['results'] == [True] * 4
    assert result['source']['endpoint_profile_does_not_evaluate_process_or_cause']
    assert result['source']['unknown_assessment_and_causal_evidence_refused']


def test_each_newly_capable_person_needs_their_own_bound_witness(result):
    rows = result['source']['cases']
    assert rows['wrong_witness']['results'] == [True, True, True, False]
    assert rows['two_gainers_one_witness']['results'] == [True, True, True, False]
    assert rows['two_gainers_two_witnesses']['results'] == [True] * 4
    assert rows['two_gainers_one_witness']['counts'] == rows['two_gainers_two_witnesses']['counts'] == [2, 0, 0, 0]
    assert rows['already_capable']['results'] == [True, True, False, True]
    assert result['source']['no_new_gainers_does_not_imply_a_completed_new_achievement']


def test_original_ability_and_process_definitions_and_claims_are_kept():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    text, basis = source_composed()
    doc = parse(text)
    audit = audit_basis(doc, basis)
    assert (audit['primitive_count'], audit['definition_count']) == (250, 492)
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['statements']) == 15
    assert (ROOT / basis['document']).read_text(encoding='utf-8') == text


def test_saved_report_reproduces_without_certifying_source_equivalence(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert result['new_primitives'] == result['new_source_assertions'] == 0
    assert result['parent_preserved'] and result['roundtrips']
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
