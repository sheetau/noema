from scripts.check_departure_hindrance_trend import native_departure_checks,target_checks,paired_checks,temporal_checks,source_checks,structure_checks

def test_native_self_imputed_departure():native_departure_checks()
def test_same_departure_and_population():target_checks()
def test_matched_obstacle_effects():paired_checks()
def test_assessed_gradual_decline_with_rebounds():temporal_checks()
def test_same_present_opening_and_decline():source_checks()
def test_preservation_and_roundtrips():structure_checks()
