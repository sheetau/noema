from scripts import check_independent_profiles as check


def test_all_response_and_assessment_patterns_require_complete_evidence():
    result=check.generic_checks()
    assert result['truth_cases']==128
    for name in ('missing_failed_case','duplicate_success','empty','extra_case','unassessed_failure'):
        assert not result['contrasts'][name]


def test_profile_thresholds_preserve_exceptions_without_zeroing_failed_cases():
    rows=check.generic_checks()['contrasts']
    assert rows['boundary'] and rows['reverse_order'] and rows['scale_weights'] and rows['fractional_scale']
    for name in ('one_success','above_boundary','zero_threshold','over_one_threshold','negative_threshold','zero_failed_weight','negative_weight','bad_indicator'):
        assert not rows[name]


def test_profile_and_current_episode_do_not_imply_each_other():
    rows=check.source_checks()['cases'][check.CORE]
    assert rows['baseline']==[True,False,True,True]
    assert rows['actual_only']==[False,True,False,False]


def test_response_must_concern_the_same_person_presented_topic_and_anchor():
    rows=check.source_checks()['cases'][check.CORE]
    for name in ('wrong_person','wrong_topic','judgment_other_topic','not_presented','wrong_anchor'):
        assert rows[name]==[False,False,False,False]
    assert rows['other_person_threshold']==[True,False,False,False]


def test_appointed_people_share_profiles_and_future_anchors_are_not_fixed_to_now():
    rows=check.source_checks()['cases'][check.CORE]
    for name in ('one_profile','one_appointed','split_people'):assert rows[name]==[True,False,False,False]
    assert rows['changing_people']==[True,False,True,True]
    assert rows['lost_future_profile']==rows['empty_future']==[True,False,True,False]


def test_unknown_inputs_are_refused_and_ordinary_eager_evaluation_agrees():
    result=check.source_checks()
    assert len(result['unknown_inputs_refused'])==2
    assert result['unlowered_uncached_profile_agrees']
    assert check.generic_checks()['unlowered_uncached_positive_and_negative_agree']


def test_actual_judgment_keeps_reasons_and_no_new_unqualified_assertions_are_added():
    result=check.judgment_checks()
    assert result['actual_h5c_and_rcr_executed']
    assert not result['cases']['missing_reason'] and not result['cases']['guided_by_other']
    result=check.structure()
    assert result['new_definitions']==6 and result['new_primitives']==result['new_assertions']==0
    assert result['previous_15_statements_unchanged']
