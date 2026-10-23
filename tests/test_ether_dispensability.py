from scripts.check_ether_dispensability import vector_checks,negation_checks,dispensability_checks,forecast_checks,structure_checks

def test_valid_velocity_vectors_include_zero():assert vector_checks()['zero_vector_included']
def test_both_scoped_negations_with_same_targets():assert negation_checks()['native_local_integration']
def test_dispensability_without_nonexistence():assert dispensability_checks()['not_a_nonexistence_claim']
def test_qualified_future_result_is_not_completed_proof():assert forecast_checks()['future_establishment_not_completed_proof']
def test_preserved_readings_and_whole_fourth_sentence():assert structure_checks()['prior_reviews_preserved']
