from scripts import check_question_discourse as checks


def test_closed_questions_and_focus_properties_keep_the_same_candidate_and_context():
    assert checks.content_checks()['same_fixed_context_for_properties_and_questions']


def test_question_attribution_preserves_contrast_conjecture_emphasis_and_response():
    assert checks.discourse_checks()['conjecture_and_focus_scopes_preserved']


def test_questions_and_their_focus_keep_rank_two_descriptions():
    assert checks.quotation_checks()['question_and_focus_descriptions_rank_two']


def test_bounded_reading_preserves_old_judgments_and_roundtrips():
    assert checks.structure_checks()['new_reviewed_sentence_characters'] == 92
