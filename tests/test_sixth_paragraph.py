from scripts.check_sixth_paragraph import coverage_checks,transition_checks,preservation_checks


def test_every_nonblank_source_position_is_covered_once():
    assert coverage_checks()['whole_paragraph_nonblank_characters']==3549


def test_all_twelve_sentences_share_context_and_preserve_question_answer_order():
    assert len(transition_checks()['all_sentence_order_edges'])==12


def test_sentence_meanings_and_existing_whole_unit_judgments_remain_unchanged():
    assert preservation_checks()['no_manuscript_or_language_changes']
