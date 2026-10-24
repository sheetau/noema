from scripts.check_distant_wave_source import geometry_checks,support_checks,binding_checks,numeric_checks,witness_checks,presentation_checks,structure_checks

def test_geometry():assert geometry_checks()['origin_neighborhood_outer_bound_and_persistent_time_interval']
def test_support():assert support_checks()['nonempty_all_physical_source_points_and_same_context']
def test_binding():assert binding_checks()['source_wave_process_fields_units_region_and_tolerance_shared']
def test_numeric():assert numeric_checks()['six_component_shared_phase_and_two_bounds_connected']
def test_witness():assert witness_checks()['one_complete_setting_not_independent_fragment_witnesses']
def test_presentation():assert presentation_checks()['hypothesis_not_actual_experiment_and_following_display_bound']
def test_structure():assert structure_checks()['old_363_statements_preserved']
