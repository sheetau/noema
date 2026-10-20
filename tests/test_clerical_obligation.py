from scripts.check_clerical_obligation import (
    native_checks, identity_checks, scope_checks, discourse_checks, unknown_checks, structure_checks)


def test_native_duty_and_appointment_are_independent_without_teaching_execution(): native_checks()


def test_same_policy_bindings_reference_and_polarity_in_both_clauses(): identity_checks()


def test_all_nine_case_arguments_and_both_conclusions(): scope_checks()


def test_attribution_reason_parallelism_and_order_without_world_truth(): discourse_checks()


def test_unknown_norm_appointment_and_discourse_inputs_rejected(): unknown_checks()


def test_prior_meanings_reviews_full_reading_and_roundtrips(): structure_checks()
