from scripts import check_collective_retention as checks


def test_joint_constraint_retention_and_causation_are_independent():
    assert checks.causal_checks()['independent_condition_combinations'] == 64


def test_source_state_is_the_same_immaturity_throughout():
    assert checks.source_checks()['source_specialization_is_existing_bf']


def test_reporting_a_constraint_does_not_assert_it_happened():
    assert checks.quote_checks()['all_world_inputs_unknown_without_execution']


def test_existing_reviews_and_generic_composability_survive():
    assert checks.structure_checks()['preserved_sentence_characters'] == 382
