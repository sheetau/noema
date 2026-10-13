import json

import pytest

from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_open_access import REPORT, build_report
from scripts.compose_open_access import ROOT, PARENT, generic_composed, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_permission_and_consistent_nonempty_successful_method_assessment_are_all_required(result):
    assert result['generic']['method_state_cases'] == 512
    assert result['generic']['accepted_access_cases'] == 9
    assert result['generic']['message_truth_not_evaluated']


def test_permission_and_usable_method_must_be_the_same_method(result):
    rows = result['source_cases']['cases']
    assert rows['baseline'] == [True, True, False]
    assert rows['split_method'] == rows['one_person_without_means'] == rows['no_means'] == [True, False, False]


def test_actual_readership_does_not_define_admission_or_access(result):
    rows = result['source_cases']['cases']
    assert rows['actual_receipt'] == [True, True, True]
    assert rows['actual_without_permission'] == [False, False, True]
    assert rows['baseline'] == [True, True, False]


def test_permission_requires_positive_grant_and_respects_the_specified_source(result):
    rows = result['source_cases']['cases']
    for name in ('no_permission', 'conflicting_rule', 'wrong_authority', 'wrong_permission_channel',
            'wrong_permission_subject', 'wrong_permission_description', 'wrong_permission_time'):
        assert rows[name] == [False, False, False]
    assert rows['other_authority_denies'] == [True, True, False]


def test_selected_outcomes_cannot_be_empty_invalid_or_only_sometimes_successful(result):
    rows = result['source_cases']['cases']
    for name in ('empty_selection', 'no_outcomes', 'selection_outside_outcomes', 'lucky_outcome_only'):
        assert rows[name] == [True, False, False]
    assert rows['unselected_failure'] == [True, True, False]


def test_shrinking_the_audience_can_hide_exclusion_and_is_not_a_proof_of_publicity(result):
    rows = result['source_cases']['cases']
    assert rows['invited_only'] == rows['empty_scope'] == [False, False, False]
    assert rows['narrowed_to_invited'] == [True, True, False]
    assert result['source_cases']['independence_and_adequacy_of_audience_remain_a_caller_contract']
    assert not result['alignment']['full_semantic_equivalence']


def test_receipt_keeps_the_same_channel_subject_and_message(result):
    rows = result['source_cases']['cases']
    assert len(rows) == 25
    for name in ('wrong_receipt_channel', 'wrong_received_subject', 'wrong_received_description'):
        assert rows[name] == [True, False, False]


def test_admission_can_be_checked_without_ability_or_receipt_but_not_without_permission(result):
    assert result['source_cases']['admission_does_not_evaluate_methods_receipt_or_understanding']
    assert result['source_cases']['unassessed_permission_refused']


def test_no_new_actual_public_access_claim_is_added():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    for builder, counts in ((generic_composed, (0, 7)), (source_composed, (233, 394))):
        text, basis = builder()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['statements']) == 15


def test_saved_report_is_reproduced_without_full_source_equivalence_claim(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert result['alignment']['unit'] == 'kant-1784:u0012'
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
