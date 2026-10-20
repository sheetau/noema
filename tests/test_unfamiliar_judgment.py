from scripts import check_unfamiliar_judgment as checks


def test_free_activity_kind_does_not_require_uncertainty_or_one_topic():
    assert checks.kind_checks()['kind_drops_topic_identity_and_uncertainty']


def test_experience_contribution_and_current_settling_are_distinct():
    assert checks.familiarity_checks()['experience_contribution_and_settling_distinguished']


def test_cause_requires_same_contents_and_differs_from_explanatory_adoption():
    assert checks.cause_checks()['adopted_explanation_is_not_causal_contribution']


def test_reasoned_conditional_uses_the_same_person():
    assert checks.conditional_checks()['same_person_and_nonvacuous_conditional']


def test_native_departure_and_causal_consequence_share_one_world():
    assert checks.native_checks()['native_departure_familiarity_judgment_and_cause_executed']


def test_quoted_reasoned_conditional_does_not_execute_world_contents():
    assert checks.quotation_checks()['closed_reasoned_conditional_quotable_without_world_evaluation']


def test_existing_judgments_and_notations_are_preserved():
    assert checks.structure_checks()['candidate_not_asserted']
