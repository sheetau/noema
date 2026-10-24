from scripts.check_wave_display import equation_checks,vector_checks,normal_checks,quantifier_checks,binding_checks,witness_checks,presentation_checks,structure_checks

def test_equations():assert equation_checks()['each_of_six_components_and_seventh_phase_equation_distinguished']
def test_vectors():assert vector_checks()['signed_three_component_vectors_and_nonnegative_norms']
def test_normal():assert normal_checks()['equal_phase_at_same_time_iff_displacement_orthogonal_to_unit_normal']
def test_quantifier():assert quantifier_checks()['all_four_coordinates_and_all_seven_position_pair_slots_quantified']
def test_binding():assert binding_checks()['all_35_setting_slots_keep_prior_physical_approximation']
def test_witness():assert witness_checks()['same_complete_setting_for_display_and_explanation']
def test_presentation():assert presentation_checks()['display_and_hierbei_elaborate_same_hypothesis_not_new_experiments']
def test_structure():assert structure_checks()['old_364_statements_preserved']
