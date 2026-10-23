from scripts.check_point_position import rest_checks,geometry_checks,measurement_checks,possibility_checks,presentation_checks,structure_checks

def test_material_point_rest_over_whole_context_interval():assert rest_checks()['return_motion_interior_detected']
def test_cartesian_record_with_signed_projections():assert geometry_checks()['same_physical_record']
def test_calibration_rigidity_and_all_used_rulers():assert measurement_checks()['nonempty_all_rulers_required']
def test_possible_execution_and_universal_conditional():assert possibility_checks()['possible_execution_not_actual_reference_measurement']
def test_author_assertion_and_source_order():assert presentation_checks()['quoted_content_not_executed']
def test_source_and_inherited_reviews():assert structure_checks()['prior_reviews_preserved']
