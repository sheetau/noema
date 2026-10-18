from scripts.check_emancipated_transmission import generic_checks,source_checks,future_checks,native_profile_checks,unknown_checks,structure


def test_prior_completion_and_first_start_share_one_ordered_history():
    assert generic_checks()['order_and_history_cases']==48


def test_the_original_sender_has_completed_native_self_achievement_before_sending():
    assert source_checks()['source_definitions_not_replaced']


def test_only_future_recipient_completions_count_in_the_same_frame():
    assert future_checks()['future_applies_to_recipient_completion']


def test_self_achievement_and_the_concrete_recipient_profile_execute_together():
    assert native_profile_checks()['departure_and_assessed_recipient_profile_executed_together']


def test_unknown_departure_and_future_inputs_remain_unknown():
    assert unknown_checks()['unknown_inputs_refused']==8


def test_prior_meanings_and_reviewed_statements_are_preserved():
    assert structure()['new_primitives']==0
