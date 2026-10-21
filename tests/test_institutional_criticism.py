from scripts.check_institutional_criticism import candidate_checks,permission_checks,individual_scope_checks,citizenship_checks,structure_checks

def test_written_scholarly_remarks_on_same_institution_without_extra_purpose():
    r=candidate_checks();assert sum(r['native_same_regime_nonempty_written_remarks'].values())==1
    assert r['execution_permission_defect_truth_and_reader_judgment_goal_not_required']

def test_making_presenting_and_joint_permissions_each_remain_conflict_free():
    r=permission_checks();assert len(r['all_three_permissions_and_separate_conflicts'])==64
    assert sum(x['value'] for x in r['all_three_permissions_and_separate_conflicts'])==1
    assert not any(r['same_target_norms'].values()) and r['content_not_executed']

def test_nonempty_full_candidate_scope_and_six_corresponding_choices():
    r=individual_scope_checks();assert len(r['nonempty_all_candidates'])==16
    assert len(r['six_choice_positions'])==36 and sum(r['six_choice_positions'])==6

def test_each_current_citizen_and_same_order_at_same_point():
    rows=citizenship_checks()['all_citizens_at_each_point_and_same_order']
    assert rows['baseline']==[True,True] and rows['new_member_denied']==[True,False]
    assert rows['departed_member']==[True,True] and rows['split_points']==[False,False]

def test_prior_meanings_and_102_main_statements_preserved():
    r=structure_checks();assert (r['new_definitions'],r['new_primitives'],r['preserved_manuscript_statements'])==(6,5,102)
