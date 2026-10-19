from scripts.check_directed_purpose import truth_checks, scope_checks, source_checks, structure


def test_direction_and_shared_goal_are_separate_conditions():
    assert len(truth_checks()['combinations']) == 128


def test_direction_keeps_people_action_goal_and_context_bound():
    assert scope_checks()['success_failure_unknown_independent']


def test_source_comparison_executes_current_definitions_without_adoption():
    assert source_checks()['contrasts']['mixed'] == [True, False]


def test_existing_claims_and_review_selections_are_unchanged():
    assert structure()['preserved_review_selections'] == 11
