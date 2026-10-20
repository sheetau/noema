from scripts import check_qualified_private_influence as checks


def test_same_goal_extent_bound_and_zero_tolerance_order():
    assert checks.extent_checks()['zero_tolerance_matches_old_order']


def test_every_solution_requires_a_correspondence_before_bounding_losses():
    assert checks.matched_checks()['combinations'] == 144


def test_native_extent_and_intervention_comparison_are_connected():
    assert checks.native_checks()['native_interventions_matches_extent_and_bound']


def test_policy_and_complete_withdrawal_share_demands_and_period():
    assert checks.policy_checks()['full_same_table_and_period_release_required']


def test_existing_meanings_and_active_manuscript_remain_unchanged():
    assert checks.structure_checks()['active_manuscript_unchanged']
