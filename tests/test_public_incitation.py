from scripts import check_public_incitation as checks


def test_appeal_reception_affect_motivation_and_causation_are_independent():
    assert checks.component_checks()['independent_conditions'] == 128


def test_same_senders_recipients_and_action_are_required():
    assert checks.group_checks()['same_senders_recipients_and_prospective_action']


def test_incitation_does_not_already_assert_the_requested_action():
    assert checks.quotation_checks()['requested_action_and_participation_not_executed']


def test_full_condition_uses_native_incitation_and_checks_the_consequence():
    assert checks.integration_checks()['all_three_original_function_arguments_filled']


def test_existing_reviews_survive():
    assert checks.structure_checks()['preserved_sentence_characters'] == 382
