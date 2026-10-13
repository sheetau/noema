import json

import pytest

from noema.grammar import parse
from scripts.check_assessed_payments import REPORT, build_report
from scripts.compose_assessed_payments import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_remittance_does_not_require_an_exchange_for_services(result):
    rows = result['transfers']['cases']
    assert len(rows) == 8
    assert next(row['results'] for row in rows if row['states'] == [True, True, False]) == [True, False]
    assert result['transfers']['self_transfer_rejected']
    assert result['transfers']['no_service_consideration_needed']


def test_obligation_fulfillment_and_speech_are_independent(result):
    rows = result['source']['cases']
    assert len(rows) == 32
    for row in rows:
        required, allowed, forbidden, paid, spoken = row['states']
        assert row['results'] == [required, required and not paid, required and spoken,
            required and allowed and not forbidden, paid, spoken, False]
    assert result['source']['standalone_agrees']


def test_normative_targets_preserve_source_person_role_action_description_and_context(result):
    rows = result['source']['contrasts']
    for name in ('required_issuer', 'required_person', 'required_role', 'required_action', 'required_description', 'required_context'):
        assert rows[name] == [False, False, False, False, True, True, False]


def test_actual_remittance_must_match_the_required_transfer(result):
    rows = result['source']['contrasts']
    for name in ('moved_transfer', 'moved_payer', 'moved_receiver', 'moved_medium', 'moved_context', 'unaccepted_medium'):
        assert rows[name] == [True, True, True, True, False, True, False]


def test_public_classification_and_permission_are_distinct(result):
    rows = result['source']['contrasts']
    for name in ('private_audience', 'missing_reader', 'speech_is_official', 'criticism_description'):
        assert rows[name] == [True, False, False, False, True, True, False]
    assert rows['wrong_authority'] == [True, False, True, False, True, True, False]
    assert len(rows) == 17


def test_criticism_does_not_require_true_content_or_a_completed_payment(result):
    assert result['source']['norms_do_not_require_payment_speech_or_criticism_truth']
    assert result['source']['unknown_performance_and_criterion_refused']
    assert result['source']['entrusted_office_not_required']


def test_suitability_and_justice_use_separate_extensible_criteria(result):
    rows = result['criticism']['cases']
    assert len(rows) == 36
    assert all(not row['result'] for row in rows if row['list_sizes'] == [0, 0])
    assert any(row['result'] for row in rows if row['suitable'] and not row['just'])
    assert any(row['result'] for row in rows if not row['suitable'] and row['just'])
    assert result['criticism']['duplicates_do_not_change_truth']
    assert result['criticism']['assertion_and_question_distinguished_even_for_false_content']


def test_payment_and_criticism_are_closed_composed_descriptions(result):
    for field, symbol in (('payment_description', 'hzah'), ('criticism_description', 'rfd')):
        description = result['source'][field]
        assert description['kind'] == 'quote'
        assert description['body']['kind'] == 'apply'
        assert description['body']['function'] == {'kind': 'function_ref', 'symbol': symbol}
        assert len(description['body']['arguments']) == 2


def test_parent_and_author_claims_are_preserved_without_new_primitives(result):
    text, basis = source_composed(); doc = parse(text)
    parent = parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['declarations']) - len(parent['declarations']) == 9
    assert len(doc['statements']) == 15
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert result['documents'][basis['document']]['primitive_count'] == 252


def test_partial_source_ranges_do_not_claim_a_complete_citizenship_or_sanctions_theory(result):
    segments = result['alignment']['segments']
    assert len(segments) == 2
    assert all(row['unit'] == 'kant-1784:u0012' and row['status'] == 'partial' for row in segments)
    assert not result['alignment']['semantic_completion']
    assert result['alignment']['normative_noncontravention_not_yet_equated_with_permission']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}


def test_reproducible_report_and_noema_alphabet_roundtrips(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert result['roundtrips'] and result['parent_preserved']
