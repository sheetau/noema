from scripts import check_sustained_assistance as check


def test_some_assistance_is_distinct_from_all_relevant_occasions():
    rows=check.source_checks()['cases']
    assert rows['baseline'][:3]==[True,True,False]
    for name in ('missed_second','other_helper','extra_occasion'):
        assert rows[name][:3]==[True,False,True]


def test_invalid_or_empty_temporal_scope_is_not_a_missed_assistance_event():
    rows=check.source_checks()['cases']
    for name in ('empty_scope','empty_occasions','outside_occasion','scope_hole','bad_order','work_gap','present_period','future_period'):
        assert rows[name][:3]==[False,False,False]


def test_purpose_binds_same_helper_act_recipient_work_and_description():
    rows=check.source_checks()['cases']
    for name in ('no_action','no_intention','different_act','other_recipient','other_project','reversed_bindings','different_goal','no_beneficiary_goal'):
        assert rows[name][:3]==[False,False,True]
    assert check.source_checks()['unknown_inputs_refused']==['scope','intention']


def test_assistance_does_not_require_success_or_merge_quoted_aliases():
    rows=check.goal_checks()['cases']
    assert rows['False']==[True,False,False,True]
    assert rows['True']==[True,True,False,True]


def test_generic_construction_also_accepts_a_different_work_topic():
    report=check.generic_checks()
    assert report['cases']['garden:baseline']==report['cases']['work:baseline']
    assert report['cases']['garden:missed_second'][:3]==[True,False,True]


def test_author_attribution_does_not_evaluate_support_history():
    report=check.attribution_check()
    assert report['quoted_targets']==['sewx']
    assert not report['support_claim_evaluated']
