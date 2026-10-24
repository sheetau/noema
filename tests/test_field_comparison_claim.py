from scripts.check_field_comparison_claim import setting_checks,equivalence_checks,form_checks,scale_checks,presentation_checks,structure_checks

def test_setting():assert setting_checks()['no_success_condition_in_comparison_scope']
def test_equivalence():assert equivalence_checks()['nonempty_all_candidate_situations']
def test_form():assert form_checks()['form_does_not_assert_truth_or_proportionality']
def test_scale():assert scale_checks()['same_scale_all_six_components_and_entire_region']
def test_presentation():assert presentation_checks()['claims_and_necessity_not_executed']
def test_structure():assert structure_checks()['nonproportional_solution_counterexample_preserved']
