from scripts import check_aligned_influence as checks


def test_demand_presence_and_complete_absence_are_separate_from_fulfillment():
    assert checks.demand_checks()['absence_requires_all_records_absent']


def test_intervention_is_the_same_complete_demand_group():
    assert checks.alignment_checks()['partial_withdrawal_rejected']


def test_progress_keeps_the_same_enlightenment_target():
    assert checks.target_checks()['same_public_reference_goal_and_world_mapping']


def test_native_alignment_and_effect_comparison_compose_without_invalid_nonhindrance():
    assert checks.combined_checks()['native_demand_alignment_and_comparison_composed']


def test_prior_meanings_are_preserved_without_new_completion_claims():
    assert checks.structure_checks()['new_semantically_reviewed_characters'] == 0
