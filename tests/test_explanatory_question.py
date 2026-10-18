from scripts.check_explanatory_question import candidate_checks,presentation_checks,source_checks,structure


def test_matching_extension_alone_does_not_explain_the_concept():
    assert candidate_checks()['profile_and_explanation_combinations']==512


def test_question_construction_and_answer_presentation_do_not_certify_answers():
    assert presentation_checks()['wrong_or_unknown_answer_can_be_presented']


def test_title_question_keeps_its_reference_context_and_explanatory_requirement():
    assert source_checks()['all_concept_truth_and_explanation_facts_unknown']


def test_opening_concept_and_nine_prior_review_judgments_are_preserved():
    assert structure()['nine_review_bindings_preserved']
