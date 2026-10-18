from scripts.check_transmitted_profiles import generic_checks,route_checks,native_checks,collective_checks,unknown_checks,quotation_checks,structure


def test_assessed_profiles_preserve_range_weights_and_thresholds():
    assert generic_checks()['current_episode_not_required']


def test_received_acquisition_and_later_retention_are_distinct():
    assert route_checks()['acquisition_and_retention_distinct']


def test_native_self_appraisal_and_universal_assent_are_transmitted_as_a_profile():
    assert native_checks()['profile_and_current_episode']==[True,False]


def test_exact_scope_excludes_recipients_who_lost_the_state():
    assert collective_checks()['acquired_but_lost_people_not_counted']


def test_unknown_state_cause_or_assessment_is_not_false():
    assert unknown_checks()['unknown_native_inputs_refused']==9


def test_existing_meanings_statements_and_review_bindings_are_preserved():
    assert structure()['new_primitives']==0


def test_a_claim_with_state_evaluation_uses_a_higher_quotation_rank():
    assert quotation_checks()['same_rank_claim_refused']
