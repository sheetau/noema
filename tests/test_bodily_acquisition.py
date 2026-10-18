from scripts.check_bodily_acquisition import generic_checks,acquisition_checks,bounded_checks,prospect_checks,attribution_checks,structure


def test_task_profiles_do_not_transfer_merely_equal_observed_truth():
    assert generic_checks()['equal_truth_does_not_share_task_profiles']


def test_native_capacity_changes_through_same_persons_contributing_experiences():
    assert acquisition_checks()['native_capacity_fall_and_learning_definitions']


def test_early_nonfall_cannot_supply_the_deadline_for_a_later_fall():
    assert bounded_checks()['same_completed_result_required']


def test_future_nonempty_acquisition_candidates_hold_original_count_context():
    assert prospect_checks()['original_count_context_preserved']


def test_learning_depiction_does_not_assert_actual_physical_or_mental_learning():
    assert attribution_checks()['all_world_facts_unknown']


def test_existing_manuscript_and_reviews_survive_task_indexing():
    assert structure()['nine_review_bindings_preserved']
