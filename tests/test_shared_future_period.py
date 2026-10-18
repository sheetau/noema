from scripts.check_shared_future_period import period_checks,conditional_checks,native_checks,structure


def test_forecast_uses_only_the_same_valid_future_period():
    assert period_checks()['history_and_truth_combinations']==64


def test_permission_and_forecast_evaluate_the_same_scenario_period():
    assert conditional_checks()['permission_and_forecast_combinations']==8


def test_native_closed_content_and_background_reach_the_existing_attribution():
    assert native_checks()['all_world_and_expectation_values_unknown']


def test_two_period_providers_are_derived_and_previous_content_is_preserved():
    assert structure()['remaining_provider_count']==20
