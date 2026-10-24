from scripts.check_aberration_specialization import numeric_checks,condition_checks,universal_checks,presentation_checks,structure_checks

def test_negative_ratio_and_general_rhs():assert numeric_checks()['negative_ratio_matches_zero_cosine_general_rhs']

def test_actual_right_angle_and_same_setting():assert condition_checks()['all_65_setting_roles_bound']

def test_full_general_and_restricted_quantifiers():assert universal_checks()['universal_slots_each']==61

def test_named_law_and_simple_display():assert presentation_checks()['quoted_physics_not_evaluated']

def test_source_and_old_evidence():assert structure_checks()['old_377_statements_and_judgments_preserved']
