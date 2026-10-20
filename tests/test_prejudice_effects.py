from scripts import check_prejudice_effects as checks


def test_prejudice_is_not_every_provisional_or_false_judgment():
    assert checks.judgment_checks()['claim_truth_never_executed']


def test_instilling_requires_same_received_understood_and_caused_state():
    assert checks.instilling_checks()['native_presentation_reception_understanding_and_generation']


def test_past_factor_causes_later_harm_without_requiring_current_belief():
    assert checks.adverse_checks()['prior_factor_can_have_ceased_at_later_point']


def test_harm_returns_to_the_same_originator_or_their_role_successor():
    assert checks.return_checks()['own_or_predecessor_not_both_required']


def test_prior_claims_and_reviews_survive_without_new_completion_claims():
    assert checks.structure_checks()['previous_claim_binding_unchanged']
