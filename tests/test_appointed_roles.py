from scripts.check_appointed_roles import generic_checks, source_checks, sentence_checks, activity_checks, attribution_checks, structure


def test_appointment_and_functions_belong_to_the_same_role():
    assert generic_checks()['true_combinations'] == 63


def test_nonappointed_counselor_and_cross_community_binding_are_rejected():
    assert source_checks()['previous_nonappointed_countermodel_rejected']


def test_the_whole_conditional_preserves_premise_and_consequence():
    assert len(sentence_checks()['combinations']) == 32


def test_public_activity_and_appointment_can_vary_independently():
    assert len(activity_checks()['independent_status_and_action']) == 4


def test_presentation_does_not_assert_institutional_or_action_facts():
    assert attribution_checks()['institutional_and_action_facts_unknown']


def test_reviewed_meanings_and_three_notations_are_preserved():
    assert structure()['preserved_review_meanings'] == 11
