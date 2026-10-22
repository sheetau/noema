from scripts.check_joint_petition import membership_checks,submission_checks,ability_checks,role_checks,structure_checks


def test_plural_citizens_without_unanimity_or_moving_membership():
    r=membership_checks();assert sum(r['anchored_plural_citizens'].values())==3


def test_same_act_content_bindings_recipient_and_each_voice():
    r=submission_checks();assert sum(r['shared_submission'].values())==3
    assert not any(r['same_arguments'].values()) and r['proposal_body_not_executed']


def test_possible_available_submission_is_not_guaranteed_success():
    r=ability_checks();assert sum(r['available_possible_shared_submission'].values())==3
    assert not any(r['same_method_and_outcome_context'].values()) and r['native_xb_and_timeline']


def test_monarch_is_same_institution_unique_appointed_highest_holder():
    r=role_checks();assert sum(row[0] for row in r['contrasts'].values())==1 and not r['semantic_boundaries']


def test_preserved_meanings_and_manuscript():
    r=structure_checks();assert (r['new_definitions'],r['new_primitives'],r['preserved_manuscript_statements'])==(3,5,102)
