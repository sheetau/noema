from scripts.check_moving_field_definition import response_checks,calibration_checks,content_checks,principle_checks,presentation_checks,structure_checks

def test_signed_response():assert response_checks()['all_four_coordinates_shared']
def test_physical_calibration():assert calibration_checks()['all_nine_witness_slots_distinguished']
def test_content():assert content_checks()['conditional_not_unconditional_truth']
def test_principle():assert principle_checks()['same_theory_not_two_separate_witnesses']
def test_presentation():assert presentation_checks()['quoted_fields_and_principle_not_executed']
def test_structure():assert structure_checks()['moving_fields_not_identified_with_calculated_mixtures']
