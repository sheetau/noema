"""Regression tests for cross-clause references and hypothetical scope."""
import pytest

from scripts.check_footnote_joint import (
    EXPECTED_FALSE, document, evaluate, model, validate_audit,
)


@pytest.mark.parametrize('variant,false_indices', EXPECTED_FALSE.items())
def test_all_six_statements_share_one_interpretation(variant, false_indices):
    doc = document()
    assert evaluate(doc, model(doc, variant)) == [i not in false_indices for i in range(6)]


def test_unknown_hypothetical_receipt_is_not_actual_nonreceipt():
    doc = document()
    with pytest.raises(ValueError, match='Unknown'):
        evaluate(doc, model(doc, 'unknown_branch_receipt'))


def test_audit_is_complete_as_an_inventory_but_not_a_positive_review():
    audit = validate_audit()
    assert audit['decision'] == 'incomplete'
    assert len(audit['clauses']) == 9
    assert audit['not_required_for_expression']
