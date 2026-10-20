from scripts import check_public_comparison_claim as checks


def test_contextual_public_is_a_public_address_without_requiring_actual_freedom():
    assert checks.public_checks()['intended_public_address_not_actual_receipt_or_permission']


def test_extent_uses_the_complete_population_and_a_fixed_exact_ratio_criterion():
    assert checks.extent_checks()['complete_population_and_exact_ratio_executed']


def test_all_comparison_inputs_and_extent_share_the_same_public_reference():
    assert checks.binding_checks()['all_fifteen_parameters_bound']


def test_generalization_keeps_all_selected_publics_and_prior_individuals():
    assert checks.quantifier_checks()['all_prior_individuals_compared']


def test_the_new_source_assertion_is_closed_and_does_not_execute_world_facts():
    assert checks.attribution_checks()['source_assertion_closed']


def test_existing_thirteen_reviews_survive_the_added_core_claim():
    assert checks.structure_checks()['preserved_whole_unit_reviews'] == 13
