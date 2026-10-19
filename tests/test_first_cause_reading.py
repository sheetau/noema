from scripts.check_first_cause_reading import population_checks,composition_checks,attribution_checks,integrity_checks


def test_population_ratio_and_demonstrative_target_share_the_qualifying_property():
    assert population_checks()['qualifying_nonmember_not_target']


def test_the_same_cohort_methods_costs_and_causes_are_bound_together():
    assert composition_checks()['cohort_change_changes_role_obligation']


def test_attribution_does_not_assert_the_causes_or_natures_speech():
    assert attribution_checks()['all_claimed_facts_unknown']


def test_nine_clauses_bind_the_judgment_to_the_current_two_statements():
    assert integrity_checks()['new_whole_unit_reviews']==0
