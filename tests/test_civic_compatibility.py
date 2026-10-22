from scripts.check_civic_compatibility import comparison_checks,scope_checks,belief_checks,selection_checks,compatibility_checks,universal_checks,structure_checks

def test_improvement_is_strict_with_exact_comparison_bindings():
    assert sum(comparison_checks()['strict_not_equal_incomparable_or_nonreflexive'].values())==1

def test_transition_scope_keeps_all_six_targets():
    assert scope_checks()['all_six_transition_bindings']==list(range(6))

def test_believing_improvement_does_not_execute_its_comparison():
    assert belief_checks()['actual_comparison_and_realization_not_executed']

def test_genuine_and_believed_improvement_are_inclusive_alternatives():
    assert selection_checks()['inclusive_genuine_or_believed']['(False, True)']

def test_change_and_whole_civil_order_share_one_possible_situation():
    assert not compatibility_checks()['same_possible_situation_for_change_and_every_order_condition']['split_conditions']

def test_all_changes_are_covered_without_hiding_invalid_names():
    assert not universal_checks()['all_changes_fixed_context_and_nonvacuous_name_validation']['invalid_name']

def test_prior_main_and_pinned_evidence_remain_unchanged():
    assert structure_checks()['preserved_main_statements']==106
