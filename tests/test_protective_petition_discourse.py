from scripts.check_protective_petition_discourse import policy_checks,binding_checks,submission_checks,metonymy_checks,discourse_checks,structure_checks


def test_principal_purpose_and_reservation_preserve_same_policy():
    r=policy_checks();assert r['combined_equals_protection_and_nonhindrance']['unprotected']==[False,False,True]
    assert r['combined_equals_protection_and_nonhindrance']['hindered']==[False,True,False]


def test_exact_policy_recipient_and_congregational_case_bindings():
    r=binding_checks();assert r['wrong_lengths_rejected']


def test_native_joint_submission_keeps_same_quoted_protective_policy():
    r=submission_checks();assert sum(r['native_shared_protective_submission'].values())==1


def test_throne_depiction_does_not_replace_authority_or_require_seat():
    r=metonymy_checks();assert r['authority_and_associated_seat_are_distinct']['no_seat']==[True,False]


def test_presentation_keeps_tentative_selection_and_same_purpose_reservation():
    r=discourse_checks();assert sum(r['same_whole_purpose_selection_reservation_metonymy_and_order'].values())==1
    assert r['quoted_world_and_physical_depiction_not_executed']


def test_preserved_meanings_reports_and_manuscript():
    r=structure_checks();assert (r['new_definitions'],r['new_primitives'],r['preserved_manuscript_statements'])==(12,5,102)
