from scripts import check_generic_fetters as checks


def test_ordered_full_future_and_conditional_profile():
    assert checks.ordered_checks()['combinations']==256


def test_both_kinds_and_same_case_bindings():
    assert checks.binding_checks()['same_case_identity_and_both_kinds_required']


def test_native_capacity_and_causal_content():
    assert checks.native_checks()['native_capacity_and_causal_profile_executed']


def test_generic_claim_apposition_correction_and_depiction():
    assert checks.presentation_checks()['world_contents_not_executed_by_attribution']


def test_source_replacement_and_preserved_reviews():
    assert checks.structure_checks()['actual_lifetime_result_removed_from_current_target']
