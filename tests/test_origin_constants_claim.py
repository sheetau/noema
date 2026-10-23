from scripts.check_origin_constants_claim import numeric_checks,graph_checks,context_checks,uncertainty_checks,presentation_checks,structure_checks

def test_independent_common_constants():assert numeric_checks()['each_rhs_and_each_constant_distinguished']

def test_all_pairs_share_one_quadruple():assert graph_checks()['common_four_constants_outside_all_pairs']

def test_same_event_and_changed_context():assert context_checks()['same_current_event_frame_and_supplied_context_checked']

def test_normalized_function_candidates():assert uncertainty_checks()['agreement_at_one_speed_not_function_identity']

def test_author_conditional_presentation():assert presentation_checks()['quoted_contents_not_executed']

def test_current_definitions_and_fixed_source():assert structure_checks()['prior_whole_unit_judgment_preserved']
