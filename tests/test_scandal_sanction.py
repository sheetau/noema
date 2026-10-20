from scripts.check_scandal_sanction import (
    assessment_checks,sanction_checks,binding_checks,possible_checks,permission_checks,
    eligibility_checks,unknown_checks,structure_checks)


def test_public_example_of_disregard_for_same_strict_duty():
    assessment_checks()


def test_intentional_adverse_response_without_assessment_truth():
    sanction_checks()


def test_exact_six_bound_arguments():
    binding_checks()


def test_possible_sanction_distinct_from_actual_and_permitted():
    possible_checks()


def test_permission_nonfactive_and_consistent_at_same_source():
    permission_checks()


def test_some_institutional_sanction_is_normatively_available():
    eligibility_checks()


def test_unknown_inputs_are_rejected():
    unknown_checks()


def test_preserved_meanings_primary_source_and_roundtrips():
    structure_checks()
