from scripts.check_payment_reading import generic_checks, scope_checks, source_checks, forecast_checks, structure


def test_restricted_sufficiency_does_not_assert_truth_in_another_domain():
    assert len(generic_checks()['independent_combinations']) == 16


def test_restriction_is_bound_to_same_node_author_and_conditional_roles():
    result = scope_checks()
    assert result['contrasts']['no_marker'] == [True, False]
    assert result['unknown_inputs_refused'] == 3


def test_current_payment_and_forecast_conditions_are_not_inferred_from_presentation():
    assert source_checks()['ordinary_countermodel_agrees']


def test_future_undertakers_can_vary_without_asserting_current_completion():
    assert forecast_checks()['contrasts']['different_workers'] == [True, False]


def test_full_sentence_partitions_old_meanings_reviews_and_notations():
    assert structure()['reviewed_sentence_characters'] == 109
