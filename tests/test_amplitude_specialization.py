from scripts.check_amplitude_specialization import numeric_checks,condition_checks,universal_checks,presentation_checks,structure_checks

def test_square_ratio_and_general_form():assert numeric_checks()['general_form_at_unit_cosine_matches_special_square_ratio']

def test_same_real_angle_and_both_sides():assert condition_checks()['all_63_setting_roles_and_same_side_bound']

def test_all_universal_positions():assert universal_checks()['universal_roles_each']==59

def test_strict_form_comparison_and_relative_clause():assert presentation_checks()['strict_comparison_not_absolute_clarity_or_reverse_order']

def test_source_and_inherited_evidence():assert structure_checks()['old_381_statements_and_judgments_preserved']
