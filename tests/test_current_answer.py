import pytest

from scripts.check_current_answer import VARIANTS, document, model, evaluate, checks, structure


@pytest.mark.parametrize('variant', VARIANTS)
def test_current_answer_cannot_borrow_another_reference(variant):
    doc = document()
    assert evaluate(doc, model(doc, variant)) == [variant == 'baseline']


def test_seven_statements_unknown_relation_and_independent_correctness():
    result = checks()
    assert len(result['joint_seven_statement_contrasts']) == 19


def test_append_preserves_previous_statements_and_meaning_contracts():
    result = structure()
    assert result['new_primitive_relations'] == 0
    assert result['previous_statements_preserved'] == 24
