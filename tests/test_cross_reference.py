import pytest
from scripts.check_cross_reference import (
    ADDRESS_VARIANTS,ADDRESS_TRUE,address_document,address_model,evaluate,checks,structure,
)


@pytest.mark.parametrize('variant',ADDRESS_VARIANTS)
def test_reference_address_keeps_fields_and_scopes(variant):
    doc=address_document()
    assert evaluate(doc,address_model(doc,variant))==[variant in ADDRESS_TRUE]


def test_directive_is_not_assertion_reading_or_a_particular_reader():
    result=checks()
    assert result['unknown_address_and_action_not_evaluated_by_presentation']
    assert len(result['combined_fourteen_statement_contrasts'])==3


def test_previous_text_and_review_meanings_remain_unchanged():
    assert structure()['previous_statements_preserved']==31
