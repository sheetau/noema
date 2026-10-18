from scripts.check_falling_depiction import generic_checks,physical_checks,adapter_checks,attribution_checks,structure


def test_postural_descent_requires_the_whole_transition_not_just_low_position():
    assert generic_checks()['combinations']==512


def test_the_same_walking_attempt_has_the_fall_as_its_own_result():
    assert physical_checks()['walking_goal_content_unknown']


def test_person_and_experience_order_and_exact_arity_are_preserved():
    assert adapter_checks()['same_person_and_experience']


def test_nonliteral_presentation_does_not_assert_either_world_content():
    assert attribution_checks()['all_physical_and_intellectual_facts_unknown']


def test_existing_manuscript_and_nine_reviews_are_unchanged():
    assert structure()['nine_review_bindings_preserved']
