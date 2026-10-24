from scripts.check_portion_energy_inquiry import setting_checks,identity_checks,candidate_checks,question_checks,presentation_checks,structure_checks

def test_setting():assert setting_checks()['exact_prior_physical_conditions_without_total_energy_witnesses']
def test_identity():assert identity_checks()['all_68_setting_roles_shared']
def test_candidate():assert candidate_checks()['actual_weighted_new_frame_slice_integral_checked']
def test_question():assert question_checks()['empty_single_and_multiple_answer_questions_allowed']
def test_presentation():assert presentation_checks()['one_question_act_and_explanatory_gloss']
def test_structure():assert structure_checks()['all_389_statements_and_judgments_preserved']
