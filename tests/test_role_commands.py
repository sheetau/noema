from scripts import check_role_commands as checks


def test_appointed_role_cannot_mix_holder_role_or_institution():
    assert checks.role_checks()['same_holder_role_institution_and_point']


def test_each_command_uses_same_call_and_replacement_for_all_recipients():
    assert checks.delivery_checks()['native_same_call_and_plural_audience']


def test_roles_quarters_and_corresponding_contents_are_bound():
    assert len(checks.example_checks()['paired_roles_quarters_positive_and_commands']) == 3


def test_attributed_examples_do_not_execute_world_contents():
    assert checks.discourse_checks()['native_quotation_without_world_execution']


def test_prior_reviews_preserved_and_three_complete_sentences_bound():
    assert checks.structure_checks()['new_reviewed_sentence_characters'] == 134
