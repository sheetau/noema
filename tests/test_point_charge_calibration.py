from scripts.check_point_charge_calibration import unit_checks,geometry_checks,calibration_checks,presentation_checks,structure_checks

def test_units():assert unit_checks()['cm_dyn_second_dimensions_and_scales']
def test_geometry():assert geometry_checks()['native_three_dimensional_same_time_distance']
def test_calibration():assert calibration_checks()['same_two_amount_records_and_directed_force']
def test_presentation():assert presentation_checks()['hypothetical_calibration_explanation_not_executed']
def test_structure():assert structure_checks()['whole_unit_review_not_claimed']
