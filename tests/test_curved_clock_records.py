from scripts.check_curved_clock_records import point_checks,coverage_checks,kinematic_checks,adapter_checks,scope_checks,structure_checks

def test_current_curve_point():assert point_checks()['current_observed_record_candidate_curve_place_and_reading_shared']
def test_complete_curve_coverage():assert coverage_checks()['four_shared_witnesses_every_slot']
def test_curve_kinematics():assert kinematic_checks()['closed_polynomial_fixture_not_certified_uniform_speed']
def test_current_curve_comparison():assert adapter_checks()['unused_polygon_parameters_explicit_and_no_fake_path']
def test_curve_extension_scope():assert scope_checks()['polygon_content_and_assumed_extension_not_conflated']
def test_curve_records_preservation():assert structure_checks()['current_geometry_and_displays_do_not_assume_lag']
