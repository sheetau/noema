from scripts import check_everywhere_restriction as checks


def test_four_anchors_keep_the_same_speaker_event_role_and_command():
    assert checks.anchor_checks()['same_preceding_case_speaker_event_and_command']


def test_rulers_permission_is_preserved_while_obedience_is_required():
    assert checks.content_checks()['ruler_permission_not_turned_into_prohibition']


def test_restriction_needs_an_excluded_choice_of_the_same_recipient():
    assert checks.restriction_checks()['genuinely_excluded_same_person_choice_required']


def test_everywhere_requires_all_four_distinct_cases():
    assert checks.universal_checks()['all_four_distinct_cases_required']


def test_deictic_attribution_does_not_execute_quoted_world_contents():
    assert checks.discourse_checks()['world_and_alternative_contents_not_executed']


def test_new_sentence_preserves_all_previous_judgments():
    assert checks.structure_checks()['new_reviewed_sentence_characters'] == 39
