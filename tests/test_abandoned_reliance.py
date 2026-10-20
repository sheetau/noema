from scripts import check_abandoned_reliance as checks


def test_negative_profile_requires_valid_normal_opportunities():
    assert checks.profile_checks()['negative_profile_not_negation_of_positive']


def test_agentive_transition_preserves_state_descriptions():
    assert checks.transition_checks()['same_descriptions_for_evaluation_transition_and_cause']


def test_all_fixed_targets_and_examined_reuse():
    assert checks.source_checks()['examined_use_after_abandonment_allowed']


def test_abandonment_is_independent_of_understanding_capacity():
    assert checks.capacity_checks()['abandonment_does_not_imply_capacity']


def test_specialization_is_quotable_without_executing_content():
    assert checks.quotation_checks()['closed_antecedent_quotable_without_world_evaluation']


def test_unasserted_candidate_preserves_existing_judgments_and_notation():
    assert checks.structure_checks()['candidate_not_asserted']
