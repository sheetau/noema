from scripts.check_personal_religious_remit import norm_checks,intervention_checks,leaving_checks,remit_checks,universal_checks,adapter_checks,structure_checks

def test_unenforced_positive_and_negative_prescriptions_are_not_leaving_alone():
    assert norm_checks()['both_polarities_absent']=={'(False, False)':True,'(False, True)':False,'(True, False)':False,'(True, True)':False}

def test_actual_intervention_keeps_same_person_activity_and_religious_standing():
    assert not intervention_checks()['same_activity_actor_person_standing_and_content']['other_role']

def test_norm_absence_does_not_excuse_actual_intervention():
    assert not leaving_checks()['native_nonprescription_and_nonintervention']['(False, True)']

def test_remit_is_independent_of_actual_concern_norm_or_necessity():
    assert not remit_checks()['same_monarchical_office_and_necessary_means_matter']['inside']

def test_every_subject_kept_when_later_belief_changes_or_names_fail():
    rows=universal_checks()['all_candidates_at_fixed_reference']
    assert rows['belief_withdrawn_later']==[False,True] and rows['invalid_names_without_belief']==[False,False]

def test_closed_targets_preserve_all_binding_positions_and_ranks():
    assert adapter_checks()['exact_adapters']['r5nt']==[0,1,2,3,4]

def test_prior_main_and_evidence_unchanged():
    assert structure_checks()['preserved_main_statements']==106
