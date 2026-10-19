from scripts.check_scoped_attitude import scope_checks,attribution_checks,structure


def test_attitude_opportunities_do_not_truncate_the_state_interval():
    assert scope_checks()['finite_interval_check_does_not_certify_whole_lifetime']


def test_facts_are_not_asserted_by_author_and_figurative_attribution():
    assert attribution_checks()['all_state_attitude_and_life_inputs_unknown']


def test_existing_whole_unit_reviews_and_declaration_bodies_remain_unchanged():
    assert structure()['preserved_review_meanings']==11
