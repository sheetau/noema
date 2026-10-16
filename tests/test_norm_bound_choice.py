from scripts import check_norm_bound_choice as check


def test_normative_and_practical_and_purposive_axes_are_independent():
    result=check.checks()
    assert result['truth_combinations']==32
    assert result['actual_outcome_control_and_norm_definitions_executed']


def test_normative_source_person_role_context_and_target_are_exact():
    rows=check.checks()['contrasts'][check.FULL]
    for name in ('other_source','other_addressee','other_role','other_point','other_target','swapped_bindings','extra_binding','other_description'):
        assert rows[name]==[True,False,False,False,False,True]


def test_purpose_belongs_to_the_same_person_method_content_and_target():
    rows=check.checks()['contrasts'][check.FULL]
    for name in ('other_goal_person','other_goal_method','other_goal_point','other_goal_target','other_goal_description'):
        assert rows[name]==[True,True,False,False,False,False]


def test_a_known_witness_does_not_prove_all_norms_have_been_assessed():
    rows=check.checks()['contrasts'][check.FULL]
    assert rows['unchecked_other_outcome']==[False,True,False,True,True,False]
    assert rows['model_unchecked']==[False]*6


def test_no_prohibited_guarantee_checks_all_outcomes_not_just_the_named_goal():
    rows=check.checks()['contrasts'][check.FULL]
    assert rows['other_outcome']==[True,False,False,False,False,False]
    assert rows['contradictory_requirements']==rows['baseline']==[True,True,False,True,True,False]


def test_truth_equivalence_does_not_replace_normative_description_identity():
    result=check.checks()
    assert result['same_truth_aliases_not_substituted'] and result['actual_content_truth_independent']


def test_construction_is_nonfactive_and_unknown_evidence_remains_unknown():
    result=check.checks()
    assert result['quote_construction_nonfactive'] and result['unlowered_uncached_cases']==2
    assert set(result['unknown_inputs_refused'])=={'unknown_norm','unknown_required','unknown_aim'}


def test_possible_result_model_uses_the_normative_person_target_and_point():
    rows=check.checks()['contextual_models'][check.FULL]
    assert rows['baseline']==[True]
    for name in ('other_person_model','other_target_model','other_point_model'):assert rows[name]==[False]


def test_prior_manuscript_and_meanings_are_preserved_without_new_primitives():
    result=check.structure()
    assert result['inherited_basis_checked'] and result['previous_declarations_preserved']
    assert result['previous_statements_preserved']==15 and result['primary_sources_pinned']==2
    assert result['new_definitions']==7 and result['new_primitives']==result['new_assertions']==0
