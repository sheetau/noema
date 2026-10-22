from scripts.check_royal_despotic_support import population_checks,despotism_checks,support_checks,power_checks,degradation_checks,joining_checks,structure_checks

def test_plural_tyrants_and_exact_remaining_subjects():
    assert not population_checks()['plural_subject_subset_and_nonempty_remainder']['duplicate_one']

def test_spiritual_despotism_is_not_merely_a_clerical_title():
    assert despotism_checks()['formal_clerical_appointment_not_added']

def test_all_supporters_and_targets_can_use_different_orders():
    assert support_checks()['native_all_tyrants_and_all_remaining_subjects']['baseline']

def test_supreme_power_is_used_by_same_holder_and_act():
    assert power_checks()['same_held_supreme_office_act_and_power_use']['baseline']

def test_unworthy_use_and_support_share_the_same_order():
    assert not degradation_checks()['all_same_support_witnesses']['support_and_degradation_split']

def test_written_intervention_and_support_share_office_and_targets():
    assert not joining_checks()['same_writer_project_work_regulation_and_office']['different_offices']

def test_existing_evidence_preserved_without_full_sentence_credit():
    assert structure_checks()['verified_characters_added']==0
