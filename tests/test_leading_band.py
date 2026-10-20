from scripts import check_leading_band as checks


def test_band_requires_the_same_body_movement_and_actual_force_effect():
    assert checks.physical_checks()['native_physical_relations']


def test_both_old_and_new_opinions_use_the_same_forecast_scope():
    assert checks.scope_checks()['same_public_mass_candidate_opinions_and_times']


def test_opinion_person_action_and_time_are_shared_by_both_sides():
    assert checks.role_checks()['identical_three_positions_and_evaluation_point']


def test_literal_picture_is_attributed_without_executing_it():
    assert checks.attribution_checks()['all_world_relations_unknown_without_execution']


def test_earlier_judgments_and_definitions_are_preserved():
    assert checks.structure_checks()['old_definitions_unchanged']
