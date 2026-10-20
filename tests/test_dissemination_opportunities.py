from scripts import check_dissemination_opportunities as checks


def test_opportunities_are_explicit_nonempty_future_points_with_later_completion():
    assert checks.opportunity_checks()['invalid_opportunities_not_silently_filtered']


def test_public_permission_and_forecast_share_reference_period_and_candidate():
    assert checks.connection_checks()['shared_reference_period_and_candidate']


def test_earlier_whole_units_and_the_first_sentence_are_unchanged():
    assert checks.structure_checks()['preserved_first_sentence_characters'] == 108
