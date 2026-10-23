from scripts.check_polygon_clock_claim import path_checks,setup_checks,total_checks,scope_checks,presentation_checks,structure_checks

def test_current_polygon_corners():assert path_checks()['shared_current_corner_bindings']
def test_return_setup():assert setup_checks()['return_allows_same_initial_event_and_place']
def test_polygon_total_lag():assert total_checks()['actual_total_seconds_exact_gap_estimate_and_residual_connected']
def test_polygon_scope():assert scope_checks()['all_finite_sequences_functions_and_real_parameters_retained']
def test_polygon_presentation():assert presentation_checks()['quoted_claims_not_finitely_executed']
def test_polygon_preservation():assert structure_checks()['additional_interval_laws_outside_author_message']
