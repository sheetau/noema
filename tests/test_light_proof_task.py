from scripts.check_light_proof_task import target_checks,proof_gap_checks,compatibility_checks,presentation_checks,structure_checks

def test_current_conditional_light_target():assert target_checks()['native_complete_frame_laws_connected']

def test_no_proof_yet_is_scoped_absence():assert proof_gap_checks()['absence_not_falsity_impossibility_or_future_absence']

def test_two_principles_share_one_setting():assert compatibility_checks()['native_shared_admissible_setting']

def test_task_parenthesis_reason_and_author():assert presentation_checks()['prior_adoption_parenthesis_and_reason_connected']

def test_fixed_source_and_prior_judgments():assert structure_checks()['prior_whole_unit_judgment_preserved']
