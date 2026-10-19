from scripts import check_walking_warning as checks


def test_conditional_activity_risk():
    assert len(checks.generic_checks()['combinations'])==48


def test_bound_cases_goals_and_harm():
    assert checks.scope_checks()['unknown_inputs_refused']==4


def test_bodily_and_intellectual_warnings_are_independent():
    assert len(checks.source_checks()['conditional_combinations'])==16


def test_metaphor_attribution_does_not_assert_contents():
    assert len(checks.attribution_checks()['contrasts'])==12


def test_preserved_manuscript_and_explicit_remaining_gaps():
    assert checks.structure()['preserved_review_selections']==11
