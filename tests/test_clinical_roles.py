from scripts.check_clinical_roles import generic_checks, source_checks, task_checks, competence_checks, attribution_checks, structure


def test_function_priority_and_qualification_belong_to_one_role():
    assert len(generic_checks()['role_combinations']) == 256


def test_general_health_expertise_does_not_fill_the_clinical_role():
    assert source_checks()['actual_skill_and_judgment_unknown']


def test_clinical_judgment_keeps_actor_patient_topic_and_context():
    assert len(task_checks()['judgment_combinations']) == 16


def test_role_qualification_is_not_actual_competence():
    assert len(competence_checks()['role_skill_combinations']) == 4


def test_source_presentation_does_not_execute_clinical_facts():
    assert attribution_checks()['all_clinical_facts_unknown']


def test_existing_reviews_and_general_health_role_are_preserved():
    assert structure()['old_general_role_preserved']
