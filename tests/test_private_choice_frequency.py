from scripts import check_private_choice_frequency as checks


def test_positive_and_negative_demands_exclude_fixed_private_choices():
    assert checks.degree_checks()['compatible_choice_required']


def test_degree_and_frequency_use_separate_weights_and_fixed_scopes():
    assert checks.frequency_checks()['three_time_demand_combinations'] == 64


def test_policy_quotation_retains_ranked_demand_evaluation():
    assert checks.quotation_checks()['rank_one_refused']


def test_inherited_meanings_and_active_manuscript_are_preserved():
    assert checks.structure_checks()['active_manuscript_unchanged']
