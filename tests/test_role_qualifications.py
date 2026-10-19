from scripts.check_role_qualifications import generic_checks,source_checks,competence_checks,attribution_checks,structure

def test_role_function_and_requirement_must_share_a_role():
    assert len(generic_checks()['role_combinations'])==64

def test_source_examples_distinguish_a_helper_from_a_qualification_bearing_role():
    assert source_checks()['actual_qualification_unknown']

def test_role_status_and_actual_skill_are_independent():
    assert len(competence_checks()['independent_role_and_skill'])==4

def test_hypothetical_attribution_does_not_assert_roles_or_skills():
    assert attribution_checks()['all_role_and_task_facts_unknown']

def test_other_reviewed_meanings_and_notations_are_preserved():
    assert structure()['affected_statements']==[4]
