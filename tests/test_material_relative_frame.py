from scripts.check_material_relative_frame import (orientation_checks,projection_checks,
    witness_checks,binding_and_domain_checks,structure_checks)


def test_right_handed_frame_and_material_anchors():orientation_checks()
def test_relative_coordinate_projections():projection_checks()
def test_relative_motion_witnesses():witness_checks()
def test_pair_binding_rigidity_counterexample_and_real_domain():binding_and_domain_checks()
def test_unchanged_manuscript_and_review():structure_checks()
