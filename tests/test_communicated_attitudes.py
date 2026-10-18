from scripts.check_communicated_attitudes import generic_checks,native_checks,collective_checks,unknown_checks,quotation_checks,structure


def test_state_and_its_causal_description_cannot_diverge():
    assert generic_checks()['state_and_causal_combinations']==256


def test_received_route_causes_acquisition_of_the_same_attitude():
    assert native_checks()['native_understanding_use_attitude_checked']


def test_collective_extent_uses_fixed_readers_and_exact_acquirers():
    assert collective_checks()['fixed_audience_reference']


def test_unknown_attitudes_and_causation_remain_unknown():
    assert unknown_checks()['unknown_native_inputs_refused']==6


def test_existing_statements_meanings_and_reviews_remain_valid():
    assert structure()['seven_review_bindings_preserved']


def test_quoted_claim_respects_evaluation_ranks():
    assert quotation_checks()['rank_one_quoted_claim_evaluable']
