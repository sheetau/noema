from scripts import check_unilateral_decision as check


def test_influence_and_unilateral_control_match_all_small_truth_tables():
    result=check.checks()
    assert result['exhaustive_rule_cases']==288
    rows=result['rules'][check.LIBRARY]
    assert rows['holder']==rows['inverted_holder']==[True,True]
    for name in ('majority','unanimity','any','parity'):assert rows[name]==[True,False]
    assert rows['target']==rows['constant']==[False,False]


def test_input_membership_duplicates_and_position_do_not_create_power():
    result=check.checks()
    assert all(row==[False,False] for row in result['invalid_lists'].values())
    assert result['permutation_checked'] and result['unlowered_uncached_rule_cases']==2


def test_same_relation_really_changes_at_the_assessed_endpoints():
    rows=check.checks()['source_contrasts'][check.FULL]
    assert rows['baseline']==rows['reverse_order']==[False,True,True,True]
    assert rows['joint_after']==[False,True,True,True]
    assert rows['continues']==[True,False,True,False]
    for name in ('already_free','different_transition','unassessed_after'):
        assert rows[name]==[False,False,True,False]


def test_affected_target_participates_in_the_same_complete_decision_domain():
    rows=check.checks()['source_contrasts'][check.FULL]
    for name in ('missing_target','duplicate_input','wrong_target'):
        assert rows[name]==[False,False,True,False]


def test_invalid_endpoint_is_not_evidence_of_lost_control():
    rows=check.checks()['source_contrasts'][check.FULL]
    for name in ('invalid_after','duplicate_after','extra_after','omitted_contributor_after'):
        assert rows[name]==[False,False,True,False]


def test_causal_result_keeps_the_control_content_and_its_description():
    result=check.checks();rows=result['source_contrasts'][check.FULL]
    assert rows['cause_absent']==rows['other_description']==[False,True,True,False]
    assert result['actual_control_transition_and_causality_executed']


def test_quotation_is_nonfactive_and_unknown_inputs_are_not_negative_facts():
    result=check.checks()
    assert result['quotation_does_not_execute_content']
    assert set(result['unknown_inputs_refused'])=={'unknown_rule','unknown_contributors'}


def test_new_concepts_are_definitions_and_preserve_the_existing_manuscript():
    result=check.structure()
    assert result['inherited_basis_checked'] and result['previous_declarations_preserved']
    assert result['previous_statements_preserved']==15
    assert result['new_definitions']==9 and result['new_primitives']==result['new_assertions']==0
