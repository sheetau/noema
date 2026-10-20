from scripts.check_protected_remarks import (
    payload_checks,ban_checks,protection_checks,prior_checks,scope_checks,regulator_checks,
    quantifier_checks,discourse_checks,unknown_checks,structure_checks)


def test_execution_payload_argument_order_and_exact_lengths():
    payload_checks()


def test_ban_argument_order_polarity_and_nonfactivity():
    ban_checks()


def test_creation_submission_and_combined_activity_are_each_protected():
    protection_checks()


def test_reference_to_the_same_officer_command_case():
    prior_checks()


def test_command_case_and_scholarly_activity_share_bindings():
    scope_checks()


def test_every_relevant_regulator_is_bound_to_the_same_protection():
    regulator_checks()


def test_whole_sentence_conditional_argument_flow():
    quantifier_checks()


def test_contrast_preserves_prior_content_and_quotation():
    discourse_checks()


def test_unknown_norm_inputs_are_rejected():
    unknown_checks()


def test_old_meanings_reviews_and_notation_are_preserved():
    structure_checks()
