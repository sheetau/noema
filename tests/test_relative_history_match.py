from scripts.check_relative_history_match import (clock_checks,point_and_shape_checks,binding_checks,
    role_and_domain_checks,structure_checks)


def test_elapsed_time_and_interval_matching():clock_checks()
def test_same_points_shape_and_relative_history_snapshots():point_and_shape_checks()
def test_all_case_bindings():binding_checks()
def test_opposite_motion_rest_roles_and_real_domain():role_and_domain_checks()
def test_preserved_manuscript_and_review():structure_checks()
