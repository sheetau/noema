from scripts.check_material_shape_dimensions import occupation_checks,history_checks,transform_checks,width_checks,scope_checks,structure_checks

def test_arbitrary_material_occupation():assert occupation_checks()['containment_and_all_position_coverage_checked']
def test_complete_rest_and_moving_histories():assert history_checks()['no_ball_or_rod_restriction']
def test_native_shape_substitution_and_current_occupation():assert transform_checks()['native_affine_shape_substitution']
def test_actual_body_directional_widths():assert width_checks()['same_body_frame_time_and_axis_for_all_six_widths']
def test_all_bodies_and_shapes():assert scope_checks()['all_bodies_and_all_shape_functions']
def test_preservation_and_dependencies():assert structure_checks()['new_primitives']==0
