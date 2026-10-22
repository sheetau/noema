from scripts.check_royal_loss_comparison import baseline_checks,magnitude_checks,causal_comparison_checks,owner_checks,branch_checks,profile_checks,adapter_checks,structure_checks

def test_nonempty_equal_counterfactual_ranges():
    assert not baseline_checks()['native_nonempty_equal_full_counterfactual_ranges']['one_shared_only']

def test_wide_gap_requires_strict_order_and_unique_measurements():
    assert not magnitude_checks()['native_unique_measurements_strict_order_and_wide_gap']['wide_claim_without_order']

def test_lower_endpoint_alone_does_not_prove_greater_causal_loss():
    assert not causal_comparison_checks()['native_both_causal_losses_shared_baseline_and_greater_loss']['lower_endpoint_different_baseline']

def test_same_owner_office_and_aspect_in_both_cases():
    assert owner_checks()['same_person_held_office_community_aspect_in_both_cases']['baseline']

def test_both_intervention_branches_keep_exact_work_and_office():
    assert branch_checks()['reproof_not_a_selection_condition']

def test_every_registered_pair_must_meet_the_comparison():
    assert not profile_checks()['all_nonempty_registered_pairs']['invalid_registered_pair']

def test_exact_ten_object_binding_and_assessment_context():
    assert len(adapter_checks()['all_ten_binding_positions'])==10

def test_previous_evidence_preserved_without_premature_full_sentence_credit():
    assert structure_checks()['verified_characters_added']==0
