from scripts.check_force_motion_binding import motion_checks,witness_checks,bridge_checks,wording_checks,presentation_checks,structure_checks

def test_motion():assert motion_checks()['arbitrary_three_component_velocity']
def test_witness():assert witness_checks()['every_existential_and_free_slot_checked']
def test_bridge():assert bridge_checks()['instantaneous_rest_not_inferred_from_point_mapping']
def test_wording():assert wording_checks()['native_inverse_coordinates_and_field_mixture']
def test_presentation():assert presentation_checks()['same_author_and_order']
def test_structure():assert structure_checks()['whole_unit_completion_not_claimed']
