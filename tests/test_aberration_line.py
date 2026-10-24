from scripts.check_aberration_line import simultaneity_checks,direction_checks,limit_checks,angle_checks,binding_checks,structure_checks

def test_source_at_same_moving_time():assert simultaneity_checks()['all_four_coordinates_and_model_family_agree']

def test_two_directions_are_not_conflated():assert direction_checks()['wave_normal_and_simultaneous_line_distinguished']

def test_connecting_line_limit_uses_actual_displacement():assert limit_checks()['actual_simultaneous_displacement_matches_rescaled_limit']

def test_literal_angle_and_printed_expression():assert angle_checks()['perpendicular_source_case_disagrees_with_printed_formula']

def test_source_identity_and_all_quantified_roles():assert binding_checks()['quantified_roles']==61

def test_source_and_old_judgments_preserved():assert structure_checks()['old_375_statements_and_judgments_preserved']
