from scripts.check_service_roles import generic_checks, source_checks, action_checks, competence_checks, attribution_checks, structure


def test_advice_service_and_qualification_use_one_role():
    assert generic_checks()['role_combinations'] == 4096


def test_judgment_only_roles_do_not_supply_the_action_requirement():
    assert source_checks()['actual_actions_and_competence_unknown']


def test_provided_action_keeps_provider_recipient_occurrence_and_topic():
    assert len(action_checks()['action_combinations']) == 32


def test_actual_skills_and_role_holding_remain_independent():
    assert len(competence_checks()['independent_role_and_skills']) == 8


def test_presenting_the_source_does_not_assert_a_treatment_event():
    assert attribution_checks()['all_service_facts_unknown']


def test_reviewed_meanings_and_prior_judgment_role_are_preserved():
    assert structure()['old_judgment_role_preserved']
