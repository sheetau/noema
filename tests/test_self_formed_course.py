from scripts import check_self_formed_course as checks


def test_same_self_work_must_contribute_to_the_same_persons_reliable_course():
    assert checks.causal_checks()['time_order_and_explanation_do_not_replace_causation']


def test_causal_success_reaches_count_and_concessive_background():
    assert checks.connection_checks()['new_causal_success_used_by_counts_and_background']


def test_existing_meanings_and_explicit_reviews_survive():
    assert checks.structure_checks()['preserved_whole_unit_reviews'] == 12
