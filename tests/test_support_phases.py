from scripts.check_support_phases import truth_checks,scope_checks,counterexamples,structure


def test_contact_load_and_transfer_are_separate_facts():
    assert truth_checks()['combinations']==192


def test_missing_phases_and_foreign_bodies_cannot_supply_a_whole_episode():
    assert scope_checks()['missing_unobserved_phase_not_completed_by_finite_order']


def test_support_is_not_a_walking_or_running_classifier():
    assert counterexamples()['no_walking_running_skill_or_control_inferred']


def test_new_component_roundtrips_without_revising_the_active_manuscript():
    assert structure()['active_manuscript_unchanged']
