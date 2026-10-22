from scripts.check_personal_salvation_judgment import subject_checks,necessity_checks,belief_checks,connection_checks,structure_checks

def test_subjecthood_keeps_same_monarchical_office():
    assert not subject_checks()['same_person_monarch_office_community_and_point']['other_role']

def test_necessary_means_reject_vacuity_and_counterexamples():
    rows=necessity_checks()['native_necessary_means']
    assert not rows['counterexample'] and not rows['no_success'] and rows['not_sufficient']

def test_false_or_impossible_necessity_can_still_be_believed():
    rows=belief_checks()['fallible_judgment']
    assert rows['false_necessity']==[True,True,False] and rows['impossible_goal']==[True,True,False]

def test_action_and_subject_scope_preserve_personal_bindings():
    assert connection_checks()['all_five_subject_judgment_bindings']==[0,1,2,3,4]

def test_existing_main_and_pinned_evidence_preserved():
    assert structure_checks()['preserved_main_statements']==106
