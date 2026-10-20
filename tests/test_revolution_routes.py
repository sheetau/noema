from scripts import check_revolution_routes as checks


def test_revolution_is_a_collective_radical_attempt_not_guaranteed_success():
    assert checks.attempt_checks()['proposed_order_implementation_unknown_without_execution']


def test_same_revolutionary_event_can_cause_the_actual_withdrawal():
    assert checks.withdrawal_route_checks()['native_revolution_and_withdrawal_connected']


def test_modal_kind_cannot_come_from_another_candidate():
    assert checks.modal_checks()['category_cannot_be_borrowed_from_another_candidate']


def test_prior_reviews_and_meanings_remain_unchanged():
    assert checks.structure_checks()['old_definitions_unchanged']
