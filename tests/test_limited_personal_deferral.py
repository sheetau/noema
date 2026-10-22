from scripts.check_limited_personal_deferral import frame_checks,correspondence_checks,choice_checks,permission_checks,possibility_checks,structure_checks

def test_candidate_scope_does_not_prefilter_to_self_and_permission():
    assert frame_checks()['native_broad_candidate_frame']['baseline_other_subject']

def test_old_and_new_bounded_self_contents_have_explicit_correspondence():
    assert correspondence_checks()['bounded_self_old_new_content_correspondence']['end']==[False,False,True,True]

def test_raw_suspension_is_broader_than_its_permission_limits():
    assert choice_checks()['native_suspension_and_separate_qualification']['other_subject']==[True,False]

def test_permission_is_positive_unconflicted_and_for_same_choice():
    assert sum(permission_checks()['unconflicted_positive_permission'].values())==1

def test_possibility_and_necessary_limits_do_not_license_all_finite_periods():
    assert possibility_checks()['personal_possibilities_universal_limits_and_combination']['unending_permitted']==[True,True,False,False]

def test_imported_meanings_and_notations_are_preserved():
    assert structure_checks()['preserved_main_statements']==104
