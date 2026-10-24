from scripts.check_wave_transform_application import coordinate_checks,event_checks,wave_checks,error_checks,binding_checks,witness_checks,presentation_checks,structure_checks

def test_coordinates():assert coordinate_checks()['both_directions_and_all_four_coordinates']
def test_events():assert event_checks()['local_membership_equivalence_does_not_force_entire_process_inside']
def test_waves():assert wave_checks()['six_components_and_independent_pulled_back_phase']
def test_errors():assert error_checks()['nonzero_errors_and_cross_field_contributions_preserved']
def test_binding():assert binding_checks()['all_41_setting_roles_shared']
def test_witness():assert witness_checks()['same_37_witnesses_for_application_display_and_parameter_explanation']
def test_presentation():assert presentation_checks()['both_correct_sections_and_final_laws_used']
def test_structure():assert structure_checks()['physical_rules_use_current_wave_not_prior_section_fields']
