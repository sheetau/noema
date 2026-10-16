from scripts import check_outcome_choice as check


def test_all_small_nondeterministic_relations_match_an_independent_oracle():
    result=check.checks()
    assert result['exhaustive_two_outcome_relations']==256
    assert result['deterministic_binary_compatibility_cases']==16


def test_uniform_choice_differs_from_choosing_after_observing_the_other_side():
    rows=check.checks()['multivalued_cases'][check.FULL]
    assert rows['three_outcomes']==[True,True,True,True]
    assert rows['respond_after_observation']==[True,False,True,False]


def test_a_possible_failure_prevents_guarantee_but_extra_methods_do_not_remove_power():
    rows=check.checks()['multivalued_cases'][check.FULL]
    assert rows['nondeterministic_failure']==[True,False,False,False]
    assert rows['extra_uncertain_method']==[True,True,True,True]
    assert rows['constant']==[True,False,False,True]


def test_invalid_empty_and_unassessed_models_are_not_successful_choices():
    result=check.checks()
    assert len(result['invalid_configurations'])==11
    assert all(row==[False]*4 for row in result['invalid_configurations'].values())
    assert result['multivalued_cases'][check.FULL]['impossible_combination']==[False]*4
    assert result['singleton_not_choice']


def test_lists_are_sets_of_identified_alternatives_and_evaluation_matches():
    result=check.checks()
    assert result['list_permutation_checked'] and result['unlowered_uncached_cases']==2


def test_departure_requires_the_same_valid_relation_before_and_after():
    rows=check.checks()['source_contrasts'][check.FULL]
    assert rows['baseline']==[True,True,True]
    for name in ('already_free','continues','invalid_after','unchecked_after','outside_after','wrong_target','wrong_transition'):
        assert rows[name]==[False,True,False]


def test_comparison_fixes_the_outcome_scope_and_keeps_causal_description_identity():
    rows=check.checks()['source_contrasts'][check.FULL]
    assert rows['changed_goals_after']==rows['baseline']
    assert rows['expanded_goals_after']==rows['continues']==[False,True,False]
    assert rows['cause_absent']==rows['other_description']==[True,True,False]


def test_quotes_do_not_execute_unknown_outcomes_and_unknown_values_remain_errors():
    result=check.checks()
    assert result['quotation_nonfactive'] and result['actual_model_transition_and_causality_executed']
    assert set(result['unknown_inputs_refused'])=={'unknown_possible','unknown_checked','unknown_possible_after'}


def test_existing_meanings_and_author_statements_are_preserved():
    result=check.structure()
    assert result['inherited_basis_checked'] and result['previous_declarations_preserved']
    assert result['previous_statements_preserved']==15
    assert result['new_definitions']==10 and result['new_primitives']==result['new_assertions']==0
