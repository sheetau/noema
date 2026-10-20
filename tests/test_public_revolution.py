from scripts import check_public_revolution as checks


def test_complete_population_and_one_cause_per_public_result():
    assert checks.aggregate_checks()['same_event_candidate_cause_and_actual_result']


def test_individual_results_share_scope_but_allow_distinct_completion_points():
    assert checks.result_frame_checks()['earlier_completion_allowed']


def test_all_revolutions_and_both_result_scopes():
    assert checks.route_checks()['other_revolution_checked_even_without_withdrawal']


def test_public_quantification_and_nonfactive_attribution():
    assert checks.scope_and_attribution_checks()['world_inputs_unknown_without_execution']


def test_preserved_judgments_and_roundtrips():
    assert checks.structure_checks()['old_definitions_unchanged']
