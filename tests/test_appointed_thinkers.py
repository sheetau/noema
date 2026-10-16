from scripts import check_appointed_thinkers as check


def test_membership_status_and_property_require_the_same_people():
    result=check.generic_checks()
    assert result['truth_cases']==64
    assert result['changing_people']==[True,False,True,False,False]
    assert result['empty_scope']==[True,True,False,False,False]


def test_appointment_and_judgment_cannot_be_split_across_people_or_records():
    rows=check.source_checks()['cases'][check.CORE]
    for name in ('split_people','split_event','split_time','wrong_role','wrong_governed_group'):
        assert rows[name]==[False,False,False]
    assert rows['baseline']==[True,True,True]


def test_past_appointment_does_not_imply_current_role_or_future_plurality():
    rows=check.source_checks()['cases'][check.CORE]
    for name in ('past_only_role','no_past_delegation','present_only_appointment'):
        assert rows[name]==[False,False,False]
    for name in ('reflexive_order','cyclic_order','incomparable_order'):assert rows[name]==[False,False,False]
    assert rows['late_appointment']==[True,True,True]
    assert rows['lost_future_thinkers']==[True,True,False]
    assert rows['changing_plural_people']==[True,True,True]


def test_plurality_and_future_scope_do_not_come_from_duplicate_names_or_empty_sets():
    rows=check.source_checks()['cases'][check.CORE]
    assert rows['one_person']==rows['one_thinker']==[True,False,False]
    assert rows['duplicate_population']==[False,False,False]
    assert rows['empty_future_scope']==rows['scope_includes_anchor']==[True,True,False]


def test_actual_appointment_and_order_definitions_match_the_integration_interpretation():
    result=check.appointment_checks()
    assert len(result['cases'])==12
    assert result['actual_hzha_rpt_ta_executed'] and result['finite_order_interpretation_agrees']
    assert result['empty_history_rejected']


def test_independent_judgment_uses_actual_owned_faculty_reasons_and_guidance():
    rows=check.judgment_checks()['cases']
    assert rows['baseline'] and rows['self_guidance']
    for name in ('no_judgment','wrong_owner','missing_reason','wrong_supported_judgment','guided_by_other'):assert not rows[name]


def test_no_new_primitives_or_unqualified_author_claims_are_added():
    result=check.structure()
    assert result['new_primitives']==result['new_assertions']==0
    assert result['previous_15_statements_unchanged']
    assert len(check.source_checks()['unknown_inputs_refused'])==2
