from scripts.check_qualitative_thinkers import preference_checks,contrast_checks,native_checks,attribution_checks,structure


def test_all_three_scene_relations_and_normal_response_patterns():
    assert preference_checks()['strict_partial_orders']==19


def test_exceptions_incomparability_empty_scopes_and_unknowns():
    assert contrast_checks()['unknown_inputs_refused']==3


def test_native_independent_judgment_does_not_require_numeric_assessment():
    assert native_checks()['numerical_profile_inputs_unused']


def test_conditional_dissemination_and_background_keep_shared_attribution():
    assert attribution_checks()['world_and_preference_inputs_not_executed']


def test_old_meanings_and_review_bindings_are_preserved():
    assert structure()['independent_disposition_has_no_scoring_dependency']
