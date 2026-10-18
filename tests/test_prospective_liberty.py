from scripts.check_prospective_liberty import generic_checks,native_checks,unknown_checks,structure


def test_temporal_scope_and_event_completion_are_separate():
    result=generic_checks()
    assert result['permission_time_combinations']==64
    assert result['event_time_combinations']==128


def test_native_future_change_does_not_reuse_past_or_other_candidate_results():
    result=native_checks(progress=print)
    assert result['population_and_activity_reference_fixed']
    assert result['actual_permission_not_inferred']


def test_unknown_history_and_permission_are_not_false_conditions():
    result=unknown_checks()
    assert result['unknown_history_and_permission_refused']
    assert result['unknown_candidate_origin_refused']


def test_existing_meanings_and_reviews_remain_valid():
    result=structure()
    assert result['seven_review_bindings_preserved']
    assert result['same_candidate_origin_bound_in_validity_condition_and_goal']
