from scripts.check_relativity_conjecture import grounds_checks,epistemic_checks,restriction_and_motion_checks,structure_checks

def test_both_ground_groups_and_failed_goal():assert grounds_checks()['failed_detection_not_negated_motion']
def test_conjecture_and_restricted_establishment():assert epistemic_checks()['conjecture_truth_independent']
def test_first_order_and_unexecuted_motion():assert restriction_and_motion_checks()['full_motion_domain_refused']
def test_sentence_presentation_and_prior_reviews():assert structure_checks()['prior_reviews_preserved']
