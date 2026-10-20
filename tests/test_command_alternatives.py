from scripts import check_command_alternatives as checks


def test_military_drill_is_same_persons_actual_practice():
    assert checks.drill_checks()['same_person_practice_and_military_pattern']


def test_payment_requires_same_designated_transaction_and_accepted_medium():
    assert checks.payment_checks()['native_rfa_ti_tj']


def test_religious_belief_does_not_require_doctrine_truth():
    assert checks.belief_checks()['doctrine_truth_not_required']


def test_commands_require_both_parts_but_quotation_executes_neither():
    assert checks.combination_checks()['positive_and_negative_parts_both_required']


def test_old_judgments_and_two_reviewed_sentences_preserved():
    assert checks.structure_checks()['preserved_reviewed_sentence_characters'] == 232
