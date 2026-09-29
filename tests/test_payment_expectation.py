from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_payment_expectation import (
    alignment, attribution_checks, forecast_checks, payment_checks,
    source_checks, takeover_checks, varying_worker_checks,
)
from scripts.compose_payment_expectation import ROOT, generic_composed, source_composed


def test_payment_binds_the_same_transfer_parties_medium_and_consideration():
    rows = payment_checks()
    assert len(rows) == 12
    assert [name for name, row in rows.items() if row['payment']] == ['baseline']
    assert all(not row['service_evaluated'] for row in rows.values())


def test_forecast_is_nonempty_prospective_and_not_actual_truth():
    result = forecast_checks()
    rows = result['cases']
    assert len(rows) == 128
    assert any(row['forecast'] and not row['current_truth'] for row in rows)
    assert any(row['current_truth'] and not row['forecast'] for row in rows)
    assert all(not row['forecast'] for row in rows if not row['selected'])
    assert result['current_as_future'] == [False, True]


def test_undertaking_is_for_the_same_beneficiary_without_fixing_one_worker():
    rows = takeover_checks()
    assert len(rows) == 8
    assert [key for key, row in rows.items() if row['undertaken']] == ['baseline', 'second_worker']
    assert all(not row['work_evaluated'] for row in rows.values())
    varying = varying_worker_checks()
    assert varying['different_workers'] == {'future_undertaking': True, 'one_worker_for_every_candidate': False}
    assert varying['same_worker'] == {'future_undertaking': True, 'one_worker_for_every_candidate': True}
    assert varying['missing_second'] == {'future_undertaking': False, 'one_worker_for_every_candidate': False}


def test_integrated_source_separates_capacity_payment_thinking_and_expectation():
    result = source_checks()
    rows = result['cases']
    assert len(rows) == 16
    assert rows['baseline']['combined'] and rows['baseline']['capacity']
    assert not rows['baseline']['payment_now'] and not rows['baseline']['undertaking_now']
    assert rows['already_paid']['payment_now'] and rows['already_paid']['combined']
    assert not rows['thinking_required']['conditional']
    assert not rows['gift']['capacity'] and rows['gift']['without_own_thinking'] and rows['gift']['conditional']
    assert not rows['empty_forecast']['expectation']
    assert result['ordinary_baseline_agrees'] and not result['definitions_replaced_by_primitives']


def test_payment_sentence_is_attributed_without_evaluating_the_hypothesis():
    rows = attribution_checks()
    assert len(rows) == 6
    assert [key for key, row in rows.items() if row['statements'][-1]] == ['baseline']
    assert all(row['statements'][:4] == [True] * 4 for row in rows.values())
    assert all(not row['underlying_content_evaluated'] for row in rows.values())


def test_payment_basis_written_forms_and_source_alignment():
    for compose, counts in ((generic_composed, (0, 15)), (source_composed, (93, 125))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            canonical = format_graph(doc, notation)
            assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
    source = alignment()
    assert source['end'] - source['start'] == len(source['source'])
    assert source['status'] == 'partial_explicit_reading'
    assert not source['full_semantic_equivalence']
