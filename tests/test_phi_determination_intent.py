from scripts.check_phi_determination_intent import candidate_checks,continuation_checks,presentation_checks,structure_checks

def test_same_function_current_stage_candidates():assert candidate_checks()['current_stage_not_prior_stage']

def test_still_unknown_in_current_equations():assert continuation_checks()['current_four_equations_prior_and_now_unknown_all_required']

def test_same_function_intention_and_order():assert presentation_checks()['intention_not_completed_determination']

def test_source_and_earlier_readings():assert structure_checks()['prior_whole_unit_judgment_preserved']
