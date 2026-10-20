from scripts import check_prospective_comparison as checks


def test_individual_comparison_requires_future_causal_self_formation():
    assert checks.individual_checks()['past_success_not_reused_as_future_success']


def test_both_modal_claims_keep_the_same_population_future_and_goal():
    assert checks.modal_checks()['liberty_not_made_necessary_or_sufficient']


def test_closed_comparative_attribution_does_not_execute_the_world():
    assert checks.attribution_checks()['all_arguments_bound'] == 15


def test_saved_meanings_and_thirteen_whole_unit_reviews_are_preserved():
    assert checks.structure_checks()['preserved_whole_unit_reviews'] == 13
