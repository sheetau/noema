from scripts import check_prejudice_depictions as checks


def test_planting_depiction_requires_placement_and_purpose_but_not_growth_success():
    assert checks.planting_checks()['growth_goal_not_executed']


def test_retaliation_requires_intentional_response_and_preserves_both_targets():
    assert checks.retaliation_checks()['originator_and_predecessor_branches_preserved']


def test_metaphor_roles_are_the_same_case_roles():
    assert checks.binding_checks()['same_case_and_role_positions']


def test_attributing_the_depictions_does_not_assert_them_as_world_facts():
    assert checks.attribution_checks()['all_world_inputs_unknown_without_execution']


def test_prior_meanings_and_reviews_remain_unchanged():
    assert checks.structure_checks()['inherited_meanings_unchanged']
