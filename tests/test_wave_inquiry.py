from scripts.check_wave_inquiry import interval_checks,region_checks,family_checks,candidate_checks,presentation_checks,structure_checks

def test_interval():assert interval_checks()['native_closed_interval_order_lower_upper_time']
def test_region():assert region_checks()['moving_region_not_old_rectangular_patch']
def test_family():assert family_checks()['all_41_roles_preserve_one_hypothesis_assignment']
def test_candidate():assert candidate_checks()['corrected_interval_chain_reaches_physical_candidate_pair']
def test_presentation():assert presentation_checks()['actual_author_question_act_under_same_prior_hypothesis']
def test_structure():assert structure_checks()['historical_interval_bug_not_in_new_statement_dependencies']
