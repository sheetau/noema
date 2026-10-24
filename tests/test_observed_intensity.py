from scripts.check_observed_intensity import cycle_checks,physical_checks,condition_checks,alternative_checks,universal_checks,presentation_checks,structure_checks

def test_same_cycle_integral_and_mean():assert cycle_checks()['same_cycle_profile_offset_integral_and_intensity']

def test_calibration_and_physical_energy_flow():assert physical_checks()['physical_role_not_inferred_from_numeric_values']

def test_same_source_observer_and_two_frame_intensity():assert condition_checks()['all_66_roles_bound_to_same_models']

def test_alternative_situations_and_all_existential_slots():assert alternative_checks()['all_existential_slots']==16

def test_all_fixed_background_and_setting_quantifiers():assert universal_checks()['all_background_universal_slots']==46

def test_equations_counterfactual_boundary_and_attribution():assert presentation_checks()['quoted_boundary_not_evaluated_during_attribution']

def test_source_and_old_judgments_preserved():assert structure_checks()['old_383_statements_and_judgments_preserved']
