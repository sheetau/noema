from scripts.check_effort_agents import generic_checks, source_checks, method_checks, attribution_checks, structure


def test_effort_agent_range_does_not_change_the_method_beneficiary():
    assert len(generic_checks()['agent_range_combinations']) == 64


def test_others_effort_is_independent_of_personal_effort_free_attainment():
    assert source_checks()['ordinary_self_other_checks_agree']


def test_effort_and_success_must_belong_to_the_same_method():
    assert method_checks()['unsuccessful_idleness_not_combined_with_effortful_success']


def test_presenting_the_example_does_not_assert_anyones_effort():
    assert attribution_checks()['all_effort_facts_unknown']


def test_the_primitive_is_explained_without_disturbing_reviewed_units():
    assert structure()['net_added_primitives'] == 0
