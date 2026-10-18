from scripts.check_caused_deterrence import generic_checks,courage_checks,reaction_checks,aggregate_checks,attribution_checks,structure


def test_actual_causal_contribution_is_independent_of_adopted_explanation():
    assert len(generic_checks()['combinations'])==16


def test_courage_is_about_the_same_described_goal_without_executing_it():
    assert courage_checks()['goal_content_unknown']


def test_source_reactions_require_actual_factors_results_and_same_causal_roles():
    assert reaction_checks()['specializations_equal_generic_factive_cause']


def test_usual_deterrence_preserves_exceptions_and_requires_actual_causation():
    assert aggregate_checks()['exception_retained_in_complete_scope']


def test_author_and_expectation_background_both_use_the_revised_causal_claim():
    assert attribution_checks()['background_uses_revised_outcome_on_both_sides']


def test_old_statements_and_reviewed_units_are_preserved():
    assert structure()['nine_review_bindings_preserved']
