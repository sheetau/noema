from scripts.check_qualitative_receipt import generic_checks,response_checks,route_checks,attribution_checks,structure


def test_described_response_is_bound_to_the_same_person_and_anchor():
    assert generic_checks()['response_and_preference_combinations']==8


def test_self_appraisal_and_assent_are_required_in_the_same_scene():
    assert response_checks()['both_responses_required_in_same_scene']


def test_causal_receipt_and_retention_use_the_identical_qualitative_state():
    assert route_checks()['same_description_used_for_cause_and_state']


def test_qualitative_sender_and_recipient_states_reach_shared_attribution():
    assert attribution_checks()['world_and_norm_truth_not_executed']


def test_previous_semantics_and_review_bindings_are_preserved():
    assert structure()['qualitative_state_has_no_scoring_dependency']
