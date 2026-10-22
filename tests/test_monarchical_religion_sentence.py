from scripts.check_monarchical_religion_sentence import conditional_checks,permission_checks,scope_checks,adapter_checks,discourse_checks,structure_checks

def test_permission_is_conditional_but_both_remits_are_independent():
    rows=conditional_checks()['native_conditional_and_independent_remits']
    assert rows['(False, False, True, True)']
    assert not rows['(False, False, True, False)']

def test_normative_permission_does_not_execute_personal_nonintervention():
    assert permission_checks()['quoted_nonintervention_not_executed']

def test_scope_and_universal_coverage_do_not_preselect_success():
    assert scope_checks()['no_oversight_or_policy_success_in_scope']

def test_adapters_keep_same_actor_polity_order_and_case():
    assert adapter_checks()['inner_reference_is_evaluation_case']

def test_nur_ubrigens_and_wohl_aber_link_without_executing_quotes():
    assert discourse_checks()['quoted_policies_and_duties_not_executed']

def test_complete_source_reading_and_inherited_evidence():
    assert structure_checks()['new_reviewed_sentence_characters']==354
