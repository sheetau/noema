from scripts.check_existential_route_fields import native_checks,boundary_checks,attribution_checks,structure


def test_actual_transmission_is_required_for_the_nine_route_witnesses():
    assert native_checks()['native_departure_receipt_causality_retention_executed']


def test_unknowns_and_unrestricted_enumeration_are_not_falsehoods():
    assert boundary_checks()['unrestricted_enumeration_explicitly_refused']


def test_attribution_no_longer_requires_external_route_field_tables():
    assert attribution_checks()['remaining_branch_providers']==13


def test_local_route_witnesses_preserve_shared_departure_and_prior_meanings():
    assert structure()['departure_witnesses_shared']
