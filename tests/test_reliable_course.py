from scripts import check_reliable_course as checks


def test_current_support_is_distinct_from_reliability_in_valid_comparisons():
    assert checks.judgment_checks()['present_reason_support_does_not_imply_reliable_performance']


def test_course_checks_earlier_judgments_and_rejects_missing_comparisons():
    assert checks.episode_checks()['all_actual_episode_judgments_checked']


def test_new_course_reaches_counts_background_and_metaphor_without_old_targets():
    assert checks.connection_checks()['native_course_used_in_count_background_and_correspondence']


def test_previous_meanings_and_explicit_reviews_are_preserved():
    assert checks.structure_checks()['preserved_whole_unit_reviews'] == 12
