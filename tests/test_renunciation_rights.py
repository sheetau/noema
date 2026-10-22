from scripts.check_renunciation_rights import scope_checks,future_checks,choice_checks,rights_checks,combined_checks,structure_checks

def test_posterity_keeps_all_members_and_same_choice_anchor():
    assert scope_checks()['native_epoch_complete_posterity_and_choice_anchor']['baseline']

def test_future_inquiry_is_by_a_posterity_member_at_the_right_time():
    assert future_checks()['posterity_point_and_end_inclusive']['r5le:beta:later']

def test_renunciation_is_chosen_and_conflicts_with_any_resumption_plan():
    assert not choice_checks()['native_choice_and_no_resumption']['other_period_resume']

def test_rights_appraisal_keeps_same_conduct_without_executing_it():
    assert rights_checks()['appraisal_does_not_execute_choice']

def test_both_renunciation_cases_refer_to_the_same_protected_rights():
    assert not combined_checks()['shared_rights_and_both_conditional_branches']['wrong_protected_rights']

def test_imports_and_prior_evidence_remain_intact():
    assert structure_checks()['preserved_main_statements']==104
