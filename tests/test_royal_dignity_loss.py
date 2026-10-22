from scripts.check_royal_dignity_loss import scale_checks,measurement_checks,causal_checks,owner_checks,joining_checks,structure_checks

def test_nonempty_total_preorder_rejects_cycles_but_allows_ties():
    assert scale_checks()['native_nonempty_total_preorder']['ties']

def test_unique_measurement_and_strict_loss_do_not_accept_ties():
    assert not measurement_checks()['native_unique_measurement_and_strict_decrease']['tied_distinct_values']

def test_all_causal_baselines_not_merely_past_and_present():
    assert causal_checks()['all_fixed_comparisons_and_same_causal_contribution']['rise_from_past_but_loss_against_baseline']

def test_same_person_office_community_and_causal_activity():
    assert owner_checks()['same_ruler_office_community_aspect_and_activity']['baseline']

def test_oversight_and_loss_cannot_use_different_offices():
    assert not joining_checks()['shared_office_oversight_and_loss']['separate_offices']

def test_previous_evidence_and_no_premature_semantic_credit():
    assert structure_checks()['verified_characters_added']==0
