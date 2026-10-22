from scripts.check_congregational_choices import scope_change_checks,state_binding_checks,assent_checks,agreement_checks,retention_checks,structure_checks


def test_same_religious_community_and_changed_content_not_just_name():
    r=scope_change_checks();assert sum(r['native_religious_community'].values())==1
    assert sum(r['changed_same_arrangement_content'].values())==1


def test_all_five_content_bindings_and_exact_length():
    r=state_binding_checks();assert r['offered_binding_cases']==1024 and r['wrong_lengths_rejected']


def test_same_completed_assent_without_executing_new_arrangement():
    r=assent_checks();assert r['agreement_content_not_executed'] and not any(r['same_assent_arguments'].values())


def test_all_fixed_parties_assent_without_requiring_all_members():
    r=agreement_checks();assert sum(r['native_whole_agreement'].values())==1 and r['not_all_congregation_members_required']


def test_retention_is_positive_intention_distinct_from_future_success():
    r=retention_checks();assert sum(r['positive_retention_intention'].values())==1 and r['unexecuted_goal_can_fail_in_future']


def test_preserved_meanings_and_manuscript():
    r=structure_checks();assert (r['new_definitions'],r['new_primitives'],r['preserved_manuscript_statements'])==(7,7,102)
