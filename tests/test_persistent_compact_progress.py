from scripts.check_persistent_compact_progress import scope_checks,unending_wiring_checks,terms_checks,agreement_checks,progress_checks,structure_checks

def test_exact_bounded_scope_and_lifetime_reject_finite_unending_claims():
    assert scope_checks()['exact_bounded_scope_and_lifetime']['baseline']==[True,False,True,True]

def test_unending_branch_keeps_full_tail_and_no_finite_end():
    assert sum(unending_wiring_checks()['unending_boundary_connection'].values())==1

def test_general_terms_agree_with_old_bounded_terms_under_explicit_correspondence():
    assert terms_checks()['native_general_terms_and_bounded_content_equality']['baseline']==[True,True]

def test_actual_agreement_does_not_execute_infinite_content():
    assert sum(agreement_checks()['general_compact_same_parties_content_and_context'].values())==1

def test_barrenness_checks_all_humanity_all_pairs_and_the_endpoint():
    assert progress_checks()['all_humanity_all_pairs_including_end']['endpoint_gain']==[True,False]

def test_previous_evidence_and_notation_are_preserved():
    assert structure_checks()['preserved_main_statements']==103
