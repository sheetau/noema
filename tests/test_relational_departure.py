from scripts import check_relational_departure as check


def test_release_needs_a_real_assessed_transition_of_the_same_relation():
    result=check.checks()
    assert result['truth_cases']==64
    rows=result['event_contrasts'][check.LIBRARY]
    for name in ('already_free','relation_continues','unassessed_before','unassessed_after','missing_history','reflexive_order'):
        assert rows[name]==[False,False,False]


def test_losing_one_holder_does_not_mean_all_holders_are_absent():
    rows=check.checks()['event_contrasts'][check.FULL]
    assert rows['baseline']==[True,True,True]
    assert rows['replacement']==rows['replacement_unassessed']==[True,False,True]
    assert rows['different_holder']==[False,False,True]


def test_target_process_and_endpoints_are_shared():
    rows=check.checks()['event_contrasts'][check.FULL]
    for name in ('different_target','different_transition','different_affected'):
        assert rows[name]==[False,False,False]


def test_causal_result_executes_the_departure_definition_instead_of_an_opaque_label():
    rows=check.checks()['causal_contrasts'][check.FULL]
    assert rows['baseline']==rows['replacement']==[True,True,True]
    for name in ('already_free','different_transition','different_affected'):assert rows[name]==[True,False,False]


def test_causal_records_keep_the_same_target_result_description_and_candidate():
    rows=check.checks()['causal_contrasts'][check.FULL]
    for name in ('cause_absent','cause_at_other_scene','other_causal_target','other_result_record','second_possible'):
        assert rows[name]==[True,False,True]


def test_quotation_is_nonfactive_and_unknown_interpretations_are_refused():
    result=check.checks()
    assert result['construction_does_not_execute_result']
    assert result['actual_tg_and_causal_rfk_executed'] and result['unlowered_uncached_event_cases']==2
    assert set(result['unknown_inputs_refused'])=={'unknown_relation','unknown_assessment','unknown_cause'}


def test_existing_manuscript_and_semantic_conventions_are_preserved():
    result=check.structure()
    assert result['inherited_basis_checked'] and result['previous_15_statements_and_all_declarations_unchanged']
    assert result['new_definitions']==5 and result['new_primitives']==result['new_assertions']==0
