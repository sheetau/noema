from scripts.check_radiative_intensity import flux_checks,average_checks,scaling_checks,point_checks,quantifier_checks,binding_checks,polynomial_checks,structure_checks

def test_signed_flux_and_plane_amplitude():assert flux_checks()['cross_product_order_and_direction_retained']

def test_mean_uses_same_profile_interval_and_integral():assert average_checks()['same_profile_interval_integral_and_average']

def test_approach_scaling_and_threshold_witnesses():assert scaling_checks()['no_finite_light_speed_value_or_zero_input_divergence']

def test_strict_left_neighborhood():assert point_checks()['both_neighborhood_endpoints_excluded']

def test_nonempty_domain_and_all_outputs():assert quantifier_checks()['each_bound_gets_its_own_radius']

def test_fixed_incident_background():assert binding_checks()['same_positive_light_and_incident_are_fixed_outside_graph']

def test_general_polynomial_certificates():assert len(polynomial_checks()['lemmas'])==4

def test_old_judgments_preserved():assert structure_checks()['old_383_statements_and_judgments_preserved']
