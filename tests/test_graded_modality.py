import pytest
from scripts.check_graded_modality import VARIANTS,interpretation,model,evaluate,oracle,checks,integration


@pytest.mark.parametrize('variant',VARIANTS)
def test_qualitative_comparison_and_condition_scope(variant):
    data=interpretation(variant)
    assert evaluate(model(data))==oracle(data)


def test_order_axioms_invariance_and_unknown_values():
    result=checks()
    assert result['valid_scale_relations']==1
    assert result['duplicate_candidate_not_a_frequency_vote']


def test_definitions_compose_with_the_active_manuscript():
    assert integration()['existing_statements_preserved']==32
