from scripts import check_prejudice_forecast as checks


def test_new_and_old_opinions_share_the_same_mass_and_future_frame():
    assert checks.future_frame_checks()['same_old_new_group_origin_and_future_bound']


def test_forecast_checks_every_revolution_candidate_and_every_public():
    assert checks.scope_checks()['all_revolution_cases_and_publics_required']


def test_prediction_and_mass_tone_are_attributed_without_executing_them():
    assert checks.attribution_checks()['all_world_relations_unknown_without_execution']


def test_earlier_judgments_and_definitions_are_preserved():
    assert checks.structure_checks()['old_definitions_unchanged']
