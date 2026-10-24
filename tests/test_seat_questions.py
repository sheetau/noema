from scripts.check_seat_questions import question_checks,premise_checks,transition_checks,presentation_checks,structure_checks

def test_question():assert question_checks()['native_question_candidates_not_request_or_existence']
def test_premise():assert premise_checks()['same_bearer_concept_setting_and_world_required']
def test_transition():assert transition_checks()['rejection_distinct_from_empty_answers_false_premise_or_ignorance']
def test_presentation():assert presentation_checks()['author_claim_and_additive_content_bound_not_question_utterance']
def test_structure():assert structure_checks()['old_362_statements_preserved']
