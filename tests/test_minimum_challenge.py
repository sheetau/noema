from scripts import check_minimum_challenge as checks


def test_minimum_validates_order_without_requiring_unique_minimum():
    assert checks.minimum_checks()['fixed_task_and_tied_minima']


def test_expectation_preserves_bindings_without_executing_quoted_content():
    assert checks.expectation_checks()['explicit_actor_task_and_context_bindings']


def test_conditional_foreground_and_background_keep_each_person_and_task():
    assert checks.package_checks()['negation_preserves_background']


def test_explicit_task_content_matches_previous_fixed_task():
    assert checks.task_content_checks()['explicit_task_matches_fixed_task_content']


def test_native_causal_conditional_minimum_and_expectation_in_one_world():
    assert checks.native_checks()['native_departure_cause_minimum_and_expectation_executed']


def test_closed_package_quotation_does_not_execute_world():
    assert checks.quotation_checks()['closed_package_without_world_evaluation']


def test_existing_judgments_and_notations_preserved():
    assert checks.structure_checks()['candidate_not_asserted']
