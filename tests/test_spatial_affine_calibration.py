from scripts.check_spatial_affine_calibration import row_checks,correspondence_checks,origin_checks,calibration_checks,polynomial_checks,connection_checks,structure_checks

def test_same_matrix_rows_and_full_affine_domain():assert row_checks()['full_real_affine_extension_refused']

def test_current_correspondence_and_actual_point_values():assert correspondence_checks()['extra_bad_correspondence_rejected']

def test_actual_moving_origin_and_full_history():assert origin_checks()['origin_not_a_light_arrival_or_fixed_unit_time']

def test_variable_calibration_times_and_nonlinear_counterexample():assert calibration_checks()['five_points_alone_do_not_imply_affinity']

def test_universal_rational_actual_time_calibration():assert polynomial_checks()['actual_positive_durations_affine_row_uniqueness']['status']=='valid'

def test_whole_same_matrix_origin_and_rays():assert connection_checks()['full_function_existence_refused']

def test_prior_statements_meanings_and_judgments():assert structure_checks()['prior_whole_unit_judgment_preserved']
