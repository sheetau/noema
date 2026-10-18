from scripts.check_subgroup_dissemination import population_checks, appointment_checks, future_checks, native_checks, attribution_checks, unknown_checks, structure


def test_population_plurality_and_subgroup_overlap():
    assert population_checks()['subset_combinations'] == 512


def test_native_appointment_has_the_same_qualified_witness():
    assert appointment_checks()['contrasts']['one_guardian_one_other'] == [False, True]


def test_future_opportunities_and_witness_turnover():
    assert future_checks()['eager_and_diagnostic_agree']


def test_native_closed_content_distinguishes_population_and_subgroup_counts():
    assert native_checks()['contrasts']['missing_appointment'] == [False, True]


def test_distinct_closed_claims_are_independently_attributed():
    assert attribution_checks()['closed_arguments_unchanged'] == 33


def test_unknown_facts_are_not_completed():
    assert unknown_checks()['unknown_inputs_refused'] == 6


def test_historical_meanings_statements_and_reviews_unchanged():
    assert structure()['new_primitives'] == 0
