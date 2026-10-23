from scripts.check_material_body_motion import (scope_checks,witness_checks,coordinate_checks,
    binding_and_domain_checks,structure_checks)


def test_complete_material_population_and_history():scope_checks()
def test_same_material_point_motion_witnesses():witness_checks()
def test_native_coordinate_and_event_incidence():coordinate_checks()
def test_trajectory_binding_and_unsampled_domains():binding_and_domain_checks()
def test_preserved_manuscript_review_and_notations():structure_checks()
