from scripts.check_doppler_infinity import point_checks,quantifier_checks,binding_checks,domain_checks,presentation_checks,structure_checks

def test_real_tail_points_and_strict_bounds():assert point_checks()['strict_input_tail_and_all_output_thresholds']

def test_cofinality_and_dependent_cutoff():assert quantifier_checks()['for_each_bound_its_own_cutoff']

def test_all_setting_witnesses_and_backgrounds():assert binding_checks()['all_existential_slots']==43

def test_prior_domain_cannot_reach_negative_infinity():assert domain_checks()['printed_claim_not_certified_true']

def test_usual_view_aside_and_nonfactive_consequence():assert presentation_checks()['no_quoted_infinity_or_physics_evaluated_by_attribution']

def test_source_and_unchanged_inherited_evidence():assert structure_checks()['old_374_statements_and_judgments_preserved']
