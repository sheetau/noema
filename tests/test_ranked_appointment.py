from scripts.check_ranked_appointment import (
    independent_checks, witness_checks, identity_checks, concrete_checks, binding_checks, unknown_rank_checks, structure_checks)


def test_past_appointment_and_current_requirement_are_independent(): independent_checks()


def test_one_event_and_past_point_in_the_same_ordered_history(): witness_checks()


def test_same_ranked_target_bindings_reference_and_polarity(): identity_checks()


def test_teaching_terms_and_duty_keep_the_same_content_without_execution(): concrete_checks()


def test_ten_individual_bindings_and_reference_reach_the_teaching_target(): binding_checks()


def test_unknown_records_and_insufficient_quote_rank_are_rejected(): unknown_rank_checks()


def test_inherited_meanings_and_roundtrips(): structure_checks()
