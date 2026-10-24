from scripts.check_field_transformation_application import provenance_checks,coverage_checks,inverse_checks,premise_checks,presentation_checks,structure_checks


def test_provenance():assert provenance_checks()['same_event_for_both_records']
def test_coverage():assert coverage_checks()['all_same_event_pairs_not_only_successful_pairs']
def test_inverse():assert inverse_checks()['all_four_inverse_slots_distinguished']
def test_premise():assert premise_checks()['prior_assumption_applied_to_same_current_setting']
def test_presentation():assert presentation_checks()['rewrite_claim_does_not_execute_or_certify_conclusion']
def test_structure():assert structure_checks()['existing_insufficient_premise_counterexample_preserved']
