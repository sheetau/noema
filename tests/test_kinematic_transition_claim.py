from scripts.check_kinematic_transition_claim import summary_checks,application_checks,presentation_checks,structure_checks


def test_summary():assert summary_checks()['native_description_domain_refused']
def test_application():assert application_checks()['current_requirements_fixed_across_future_evaluation']
def test_presentation():assert presentation_checks()['summary_and_goal_quotes_not_executed']
def test_structure():assert structure_checks()['old_unfinished_mapping_and_application_not_used']
