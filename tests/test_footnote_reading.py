from scripts.check_footnote_reading import criterion_checks, source_checks, joint_checks, structure, audit


def test_content_correspondence_is_broader_than_definition_expansion_but_not_sampled_truth():
    assert criterion_checks()['automatic_general_synonym_classifier'] is False


def test_content_criterion_remains_connected_to_the_actual_modal_question():
    assert source_checks()['unknown_correspondence_refused']


def test_twelve_connected_assertions_preserve_the_question_and_reference_scope():
    assert joint_checks()['real_answers_and_comparison_left_unknown']


def test_meaning_refinement_preserves_all_syntax_and_ten_previous_reviews():
    assert structure()['preserved_review_meanings'] == 10


def test_whole_note_reading_covers_every_character_without_claiming_an_automatic_proof():
    record = audit()
    assert record['source']['range'] == [0, 462]
    assert len(record['clauses']) == 9
    assert all(c['assessment'] == 'represented_under_reading' for c in record['clauses'])
    assert record['unresolved'] == []
