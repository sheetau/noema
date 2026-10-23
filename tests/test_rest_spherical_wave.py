from scripts.check_rest_spherical_wave import numeric_checks,arrival_checks,emission_checks,front_checks,presentation_checks,structure_checks

def test_equation_and_future_front_distinct():assert numeric_checks()['squared_equation_distinct_from_future_front']

def test_same_measured_ray_and_arrival():assert arrival_checks()['same_wave_ray_emission_endpoint_segment_frame_context']

def test_all_wave_members_share_origin():assert emission_checks()['nonempty_all_constituent_rays_share_emission']

def test_full_wave_front_and_arbitrary_point():assert front_checks()['full_native_event_record_scope_and_both_directions']

def test_assumption_consequence_and_author():assert presentation_checks()['assumption_and_conditional_consequence_distinct']

def test_current_meanings_and_source():assert structure_checks()['prior_whole_unit_judgment_preserved']
