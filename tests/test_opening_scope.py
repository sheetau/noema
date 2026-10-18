from scripts.audit_opening_scope import scope_checks,causal_checks,unknown_checks,structural_checks,ability_recheck


def test_two_deficits_differ_from_either_deficit_and_negated_joint_adequacy():
    assert scope_checks()['one_missing_capacity_does_not_satisfy_both_missing']


def test_joint_cause_does_not_distribute_to_each_factor():
    result=causal_checks()
    assert result['non_distributivity_counterexamples']=={
        'joint_only':{'source_condition':True,'both_individual_causes':False},
        'individual_only':{'source_condition':False,'both_individual_causes':True}}


def test_unknown_assessment_and_unknown_joint_cause_are_not_completed():
    assert unknown_checks()['unknowns_refused']==5


def test_scope_judgment_is_bound_to_current_text_but_does_not_complete_paragraph():
    assert structural_checks()['one_subclause_judgment_not_whole_paragraph_review']


def test_ability_is_rechecked_from_current_manuscript_in_current_runtime():
    result=ability_recheck()
    assert result['models']==128 and result['matches_independent_set_conditions']
