from scripts.check_teaching_policy import (
    local_checks, period_checks, coverage_checks, binding_norm_checks, unknown_quote_checks, structure_checks)


def test_native_task_audiences_actual_presentations_and_conformity(): local_checks()


def test_positive_teaching_and_all_actual_expositions_across_each_period(): period_checks()


def test_every_recipient_assigned_and_every_task_fulfilled(): coverage_checks()


def test_same_nine_bindings_and_whole_policy_in_duty_and_appointment(): binding_norm_checks()


def test_unknown_scope_rejected_and_ranked_policy_not_executed(): unknown_quote_checks()


def test_inherited_meanings_and_roundtrips(): structure_checks()
