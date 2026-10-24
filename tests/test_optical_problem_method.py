from scripts.check_optical_problem_method import reconstruction_checks,witness_checks,method_checks,scope_checks,presentation_checks,structure_checks

def test_inverse_reconstruction():assert reconstruction_checks()['both_inverse_fields_and_entire_ordered_answer_sequence_checked']
def test_all_shared_witnesses():assert witness_checks()['all_33_shared_witness_slots_distinguished']
def test_same_physical_setting():assert method_checks()['same_setting_questions_and_all_target_roles_preserved']
def test_universal_topic_scope():assert scope_checks()['all_topic_problems_not_only_solvable_cases']
def test_three_sentence_presentation():assert presentation_checks()['quoted_physical_claims_not_assumed_true']
def test_preserved_evidence():assert structure_checks()['all_406_previous_statements_and_meanings_preserved']
