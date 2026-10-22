from scripts.check_royal_intervention_conditions import scope_checks,base_intervention_checks,conditional_checks,independent_consequences_checks,universal_checks,adapter_checks,structure_checks

def test_scope_preserves_all_targets_and_same_office_without_outcome_selection():
    assert scope_checks()['all_ten_scope_positions']

def test_basic_intervention_keeps_exact_work_project_office_and_activity():
    assert base_intervention_checks()['same_work_inquiry_office_and_intervention']['baseline']

def test_conditional_truth_tables_and_same_inner_case():
    assert conditional_checks()['comparison_range_uses_same_case_and_assessment']

def test_comparison_absence_does_not_erase_other_consequences():
    assert not independent_consequences_checks()['independent_antecedents_and_consequences']['basic_only_no_loss']

def test_all_target_positions_and_cases_are_universally_checked():
    assert not universal_checks()['all_ten_objects_and_all_cases']['second_case']

def test_discourse_adapters_preserve_exact_bindings():
    assert len(adapter_checks()['all_ten_binding_positions'])==10

def test_no_premature_full_sentence_or_main_manuscript_credit():
    assert structure_checks()['verified_characters_added']==0
