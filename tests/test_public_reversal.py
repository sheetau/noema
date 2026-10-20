from scripts import check_public_reversal as checks


def test_prior_action_needs_same_actors_and_actual_effect():
    assert checks.prior_checks()['state_without_prior_action_causation_rejected']


def test_agitators_are_a_separate_plural_cohort_with_explicit_boundaries():
    assert checks.incitation_checks()['plural_actual_participants_required']


def test_reversal_preserves_targets_and_conditional_chronology():
    assert checks.reversal_checks()['actual_retention_and_causal_definitions_executed']


def test_existing_statements_and_review_evidence_survive():
    assert checks.structure_checks()['preserved_sentence_characters'] == 382
