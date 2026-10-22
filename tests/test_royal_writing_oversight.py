from scripts.check_royal_writing_oversight import clarity_checks,attempt_checks,supervision_checks,binding_checks,adapter_checks,structure_checks

def test_nonempty_complete_clarity_target_and_canonical_items():
    assert clarity_checks()['canonical_item_not_its_alias_required']

def test_written_attempt_uses_same_record_but_does_not_execute_goal():
    assert attempt_checks()['unachieved_and_unknown_goal_not_executed']

def test_governmental_supervision_needs_office_and_same_work():
    assert supervision_checks()['no_ban_or_success_required']

def test_subjects_religious_field_and_intervention_share_arguments():
    assert binding_checks()['same_work_and_intervention']['baseline']

def test_all_seven_adapter_arguments_and_unknown_rejection():
    assert adapter_checks()['exact_length_reference_point_and_unknown_checked']

def test_inherited_evidence_and_no_premature_review_credit():
    assert structure_checks()['verified_characters_added']==0
