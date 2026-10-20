from scripts.check_officer_example import (
    profile_checks, harm_checks, obedience_checks, norm_checks, scope_checks,
    quantifier_checks, discourse_checks, unknown_checks, structure_checks)


def test_serious_loss_requires_assessed_strict_loss_in_every_solution_pair():
    profile_checks()


def test_same_discussion_and_work_in_hypothetical_execution_model():
    harm_checks()


def test_signed_obedience_requires_same_demand_and_guided_adjustment():
    obedience_checks()


def test_requirement_keeps_target_polarity_and_does_not_execute_compliance():
    norm_checks()


def test_officer_command_and_same_assigned_work():
    scope_checks()


def test_obligation_does_not_depend_on_intent_to_discuss():
    quantifier_checks()


def test_example_attribution_and_order_preserve_quotation():
    discourse_checks()


def test_unknown_harm_inputs_are_rejected():
    unknown_checks()


def test_preserved_meanings_reviews_and_transcription():
    structure_checks()
