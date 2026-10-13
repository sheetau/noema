import json

import pytest

from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_message_relays import REPORT, build_report
from scripts.compose_message_relays import ROOT, PARENT, generic_composed, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_presentation_receipt_and_understanding_have_independent_requirements(result):
    assert result['generic']['direct_state_cases'] == 32
    assert result['generic']['route_cases']['not_understood'] == [True, False]
    assert result['generic']['message_truth_and_endorsement_not_evaluated']


def test_matching_messages_do_not_establish_causal_relay_by_themselves(result):
    rows = result['generic']['route_cases']
    assert rows['baseline'] == [True, True]
    for name in ('independent_same_message', 'wrong_predecessor', 'wrong_relay_person',
            'wrong_relay_subject', 'wrong_relay_description', 'wrong_relay_time'):
        assert rows[name] == [False, False]


def test_each_intermediate_receipt_and_same_message_binding_is_required(result):
    rows = result['generic']['route_cases']
    assert len(rows) == 23
    for name in ('missing_first_receipt', 'missing_second_receipt', 'changed_subject', 'changed_force',
            'disconnected_people', 'wrong_origin', 'wrong_target', 'wrong_endpoint_time'):
        assert rows[name] == [False, False]


def test_relay_order_is_strict_but_a_person_may_receive_again_later(result):
    rows = result['generic']['route_cases']
    for name in ('reversed_steps', 'repeated_step', 'same_time', 'cyclic_history', 'missing_history', 'self_transmission'):
        assert rows[name] == [False, False]
    assert result['generic']['route_lengths'] == {str(n): [True, True] for n in (1, 2, 3)}


def test_reaching_a_group_does_not_require_all_relays_to_belong_to_it(result):
    rows = result['source_cases']['cases']
    assert rows['external_intermediary'] == [True, True, True]
    assert rows['not_understood'] == [True, False, True]
    assert rows['future_receipt'] == [False, False, False]
    for name in ('empty_audience', 'duplicate_audience', 'nonhuman_audience'):
        assert rows[name] == [True, True, False]
    assert result['generic']['audience_cases']['empty_audience'] == [False]


def test_unknown_receipt_is_refused_while_understanding_can_remain_unassessed(result):
    assert result['source_cases']['unknown_receipt_refused']
    assert result['source_cases']['understanding_not_required_for_receipt']
    assert result['source_cases']['all_unrelated_source_primitives_guarded']


def test_routes_do_not_assert_the_unwritten_message_or_actual_enlightenment():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    for builder, counts in ((generic_composed, (0, 6)), (source_composed, (229, 384))):
        text, basis = builder()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['statements']) == 15


def test_saved_report_is_reproduced_and_does_not_claim_full_source_equivalence(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert not result['alignment']['full_semantic_equivalence']
    assert result['alignment']['remaining']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
