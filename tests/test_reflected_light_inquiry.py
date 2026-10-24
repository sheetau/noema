from scripts.check_reflected_light_inquiry import return_checks,coverage_checks,setting_checks,candidate_checks,question_checks,presentation_checks,structure_checks

def test_return():assert return_checks()['both_polarizations_and_all_three_directions_returned']
def test_coverage():assert coverage_checks()['every_patch_point_through_whole_mirror_cycle_required']
def test_setting():assert setting_checks()['all_74_roles_shared_outside_candidates']
def test_candidates():assert candidate_checks()['pressure_direction_frequency_intensity_all_constrained']
def test_question():assert question_checks()['all_six_candidates_share_fixed_74_role_setting']
def test_presentation():assert presentation_checks()['closed_conditions_and_questions_not_executed']
def test_structure():assert structure_checks()['all_395_previous_statements_and_meanings_preserved']
