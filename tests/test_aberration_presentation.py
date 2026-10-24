from scripts.check_aberration_presentation import motion_checks,scope_checks,binding_checks,universal_checks,presentation_checks,structure_checks

def test_forward_phase_ray_coordinates():assert motion_checks()['forward_phase_motion_uses_light_speed_not_phase_rate']

def test_all_local_normal_pairs_and_forward_rays():assert scope_checks()['quantified_positions_checked']==12

def test_naming_witnesses_and_same_optical_setting():assert binding_checks()['naming_witnesses']==59

def test_three_quantified_contents_and_distinct_angles():assert universal_checks()['prior_a_prime_not_replaced_by_literal_line_angle']

def test_naming_parenthesis_and_display_attribution():assert presentation_checks()['quoted_physics_and_false_printed_claim_not_evaluated']

def test_source_and_inherited_evidence():assert structure_checks()['old_375_statements_and_judgments_preserved']
