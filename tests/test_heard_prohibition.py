from scripts import check_heard_prohibition as checks


def test_prohibition_negates_activity_inside_directive():
    assert checks.command_checks()['native_negative_directive']


def test_same_call_is_heard_without_executing_the_quoted_command():
    assert checks.hearing_checks()['observer_need_not_be_addressee']


def test_every_fixed_social_quarter_has_a_matching_call():
    assert checks.sides_checks()['each_fixed_quarter_requires_its_own_witness']


def test_first_sentence_context_repaired_and_second_contrast_bound():
    assert checks.discourse_checks()['old_paragraph_context_not_used']


def test_old_judgments_preserved_and_changed_first_sentence_rechecked():
    assert checks.structure_checks()['first_sentence_rechecked']
