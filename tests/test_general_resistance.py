from scripts.check_general_resistance import (
    response_checks,breadth_checks,potential_checks,domain_checks,unknown_checks,structure_checks)


def test_resistance_to_positive_and_negative_public_requirements():
    response_checks()


def test_fixed_complete_population_and_contextual_breadth():
    breadth_checks()


def test_same_possible_outcome_for_activity_cause_and_resistance():
    potential_checks()


def test_unrestricted_descriptions_not_replaced_with_finite_known_requirements():
    domain_checks()


def test_unknown_inputs_are_rejected():
    unknown_checks()


def test_preserved_meanings_primary_evidence_and_notation():
    structure_checks()
