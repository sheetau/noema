from scripts.check_posterity_harm import scope_checks,harm_checks,cause_checks,adapter_checks,presentation_checks,structure_checks

def test_complete_posterity_keeps_survivors_and_farther_generations():
    assert sum(scope_checks()['native_complete_group_and_agreement_epoch'].values())==1

def test_collective_harm_requires_same_population_and_strict_evaluated_comparison():
    assert harm_checks()['strict_collective_comparison']['equal'] is False
    assert harm_checks()['harm_not_identified_with_barrenness']

def test_second_causal_consequence_uses_same_barrenness_and_posterity():
    assert sum(cause_checks()['quoted_second_causal_link'].values())==1

def test_scope_does_not_select_successful_harmful_compacts():
    assert adapter_checks()['source_and_candidate_scope']['no_barrenness']==[False,True]

def test_conjecture_does_not_assert_quoted_consequence():
    assert sum(presentation_checks()['same_whole_scope_focus_reference_and_context'].values())==1

def test_prior_meanings_and_generalized_posterity_are_preserved():
    assert structure_checks()['old_posterity_formula_generalized_exactly']
