from scripts.check_personal_renunciation_sentence import core_checks,adapter_checks,scope_checks,depiction_checks,discourse_checks,structure_checks

def test_whole_content_keeps_both_permission_and_rights_halves():
    assert sum(core_checks()['both_halves_required'].values())==1

def test_adapters_keep_same_people_conduct_rights_and_periods():
    assert adapter_checks()['native_contempt_appraisal']

def test_personal_scope_does_not_require_existing_posterity():
    assert scope_checks()['separate_personal_posterity_and_comparison_scopes']['r5lv']['no_posterity_frame']

def test_literal_depiction_uses_the_actors_own_foot_and_same_rights():
    assert not depiction_checks()['same_actor_response_own_foot_and_rights_object']['other_foot']

def test_all_discourse_links_are_required_without_executing_quotations():
    assert discourse_checks()['quoted_literal_action_choice_and_rights_not_executed']

def test_full_source_reading_and_all_earlier_evidence_are_preserved():
    assert structure_checks()['new_reviewed_sentence_characters']==256
