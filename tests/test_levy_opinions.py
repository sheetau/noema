from scripts.check_levy_opinions import (
    content_checks, message_checks, expression_checks, public_checks, unknown_checks, structure_checks)


def test_inappropriateness_and_injustice_have_independent_fixed_conditions():
    content_checks()


def test_assertive_force_does_not_guarantee_content_truth():
    message_checks()


def test_same_person_expresses_their_own_view_of_the_same_levy():
    expression_checks()


def test_scholarly_public_use_allows_either_or_both_critical_views():
    public_checks()


def test_unknown_content_and_expression_inputs_are_rejected():
    unknown_checks()


def test_existing_meanings_evidence_and_roundtrips_are_preserved():
    structure_checks()
