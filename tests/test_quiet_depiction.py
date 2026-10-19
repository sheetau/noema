from scripts import check_quiet_depiction as checks


def test_local_absence_is_not_a_disposition_or_missing_evidence():
    assert len(checks.local_checks()['combinations'])==64


def test_motor_patterns_share_body_episode_point_and_reference():
    assert len(checks.motor_checks()['contrasts'])==7


def test_quiet_depiction_retains_actual_husbandry_and_prior_point():
    assert len(checks.source_checks()['contrasts'])==14


def test_source_presentation_does_not_assert_literal_or_inner_truth():
    assert checks.attribution_checks()['six_excerpt_statements_evaluated']


def test_meanings_readings_pins_and_notations_remain_consistent():
    assert checks.structure()['preserved_review_selections']==11
