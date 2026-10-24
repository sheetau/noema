from scripts.check_parallel_alternative_claim import numeric_checks,origin_checks,bridge_checks,method_checks,presentation_checks,structure_checks

def test_numeric():assert numeric_checks()['point_formula_domain_not_silently_restricted_to_frame_domain']
def test_origin():assert origin_checks()['nonzero_third_times_allowed']
def test_bridge():assert bridge_checks()['full_trajectory_actual_derivative_norm_and_record_line_all_required']
def test_methods():assert method_checks()['old_angle_specialization_and_all_new_bridge_steps_required']
def test_presentation():assert presentation_checks()['same_author_fifth_section_and_section_three_reference']
def test_structure():assert structure_checks()['other_statements_preserved']==355
