from scripts.check_sufficient_payment import generic_checks, source_checks, outcome_checks, attribution_checks, structure


def test_fractional_prices_and_same_payment_bindings():
    assert len(generic_checks()['amount_combinations']) == 36


def test_partial_payment_is_not_ability_to_cover_the_work():
    result = source_checks()
    assert result['countermodels']['partial']['previous'][0]
    assert not result['countermodels']['partial']['current'][0]


def test_every_selected_result_of_one_method_must_cover_the_price():
    result = outcome_checks()['contrasts']
    assert not result['one_partial'][0] and result['separate_methods'][0]


def test_attributing_the_sentence_does_not_assert_prices_or_payment():
    assert attribution_checks()['prices_and_payment_facts_unknown']


def test_old_meanings_reviewed_units_and_all_notations_are_preserved():
    assert structure()['preserved_review_meanings'] == 11
