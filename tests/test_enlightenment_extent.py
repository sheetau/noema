from scripts import check_enlightenment_extent as checks


def test_extent_and_existing_goal_use_the_same_changed_readers_and_threshold():
    assert checks.extent_checks()['threshold_equality_is_not_attainment']


def test_same_period_extent_order_preserves_zero_and_intermediate_progress():
    assert checks.order_checks()['below_threshold_progress_distinguished']


def test_invalid_audience_and_period_are_not_zero_progress():
    assert checks.guard_checks()['invalid_population_or_period_refused']


def test_only_the_same_enlightenment_goal_can_use_the_scale():
    assert checks.callback_checks()['same_closed_r2ln_required']


def test_restriction_comparison_uses_the_fixed_scale_and_rejects_missing_inputs():
    assert checks.integration_checks()['invalid_scale_is_not_nonhindrance']


def test_native_scale_and_matched_profiles_detect_progress_before_attainment():
    assert checks.native_profile_checks()['progress_does_not_require_goal_attainment']


def test_prior_meanings_and_the_new_library_roundtrip_are_preserved():
    assert checks.structure_checks()['unchanged_dependencies']
