from scripts.check_transverse_ray_claim import path_checks,trace_checks,connection_checks,equation_checks,presentation_checks,structure_checks

def test_complete_diagonal_and_transverse_paths():assert path_checks()['native_complete_K_diagonal_and_k_transverse_paths_checked']

def test_native_linear_functions_and_full_domain_refusal():assert trace_checks()['full_real_history_refused']

def test_same_current_measurements_and_distinct_axes():assert connection_checks()['axis_records_not_interchangeable']

def test_native_equations_and_same_free_coefficient():assert equation_checks()['free_phi_retained']

def test_analogy_conditions_and_substitution_presentation():assert presentation_checks()['quoted_contents_not_executed']

def test_prior_meanings_and_source_preserved():assert structure_checks()['prior_whole_unit_judgment_preserved']
