from scripts import check_limited_consequence as checks


def test_exclusion_is_local_to_one_item_and_point():
    assert checks.exclusion_checks()['other_item_and_point_not_excluded']


def test_limited_and_reliable_outcomes_share_the_same_profile():
    assert checks.profile_checks()['same_profile_arguments']


def test_concessive_cases_are_nonempty_and_actually_satisfy_the_premise():
    assert checks.concession_checks()['nonempty_candidates_must_satisfy_premise']


def test_scalar_and_concessive_backgrounds_remain_independent():
    assert checks.package_checks()['negation_preserves_both_backgrounds']


def test_native_conditional_executes_both_histories_and_allows_other_reliable_activity():
    assert checks.native_checks()['other_reliable_activity_allowed']


def test_attribution_preserves_scope_and_does_not_execute_quoted_content():
    assert checks.attribution_checks()['quoted_content_not_executed']


def test_quotation_preserves_both_closed_contents():
    assert checks.quotation_checks()['closed_package_without_world_evaluation']


def test_existing_judgments_and_notations_preserved():
    assert checks.structure_checks()['candidate_not_asserted']
