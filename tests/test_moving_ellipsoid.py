from scripts.check_moving_ellipsoid import geometry_checks,setting_checks,shape_checks,general_checks,structure_checks

def test_closed_ellipsoid_and_semiaxes():assert geometry_checks()['containment_and_full_volume_coverage_distinct']
def test_arbitrary_rest_sphere_and_motion():assert setting_checks()['no_origin_center_or_specific_body_restriction']
def test_moving_center_and_full_time_shape():assert shape_checks()['center_cx_over_beta_plus_vt_at_all_times']
def test_general_bodies_and_author_consequence():assert general_checks()['all_qualifying_bodies_not_only_one_example']
def test_preserved_prior_judgments():assert structure_checks()['prior_whole_unit_judgments_preserved']
