from scripts import check_prejudice_claim as checks


def test_terminal_means_end_of_the_fixed_relevant_process():
    assert checks.terminal_checks()['native_contextual_maximum_not_world_end']


def test_case_supply_preserves_native_causal_and_temporal_relations():
    assert checks.case_checks()['all_case_relations_evaluated_natively']


def test_every_fixed_case_and_target_is_required():
    assert checks.scope_checks()['all_cases_and_all_targets_required']


def test_self_focus_includes_successors_without_selecting_only_harmed_people():
    assert checks.focus_checks()['scope_does_not_select_by_harm']


def test_attribution_does_not_execute_the_reported_world():
    assert checks.attribution_checks()['world_inputs_unknown_without_execution']


def test_previous_meanings_and_reviews_survive():
    assert checks.structure_checks()['inherited_meanings_unchanged']
