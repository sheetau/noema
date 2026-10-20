from scripts import check_guardian_forecast as checks


def test_crowd_size_uses_the_complete_human_population():
    assert checks.crowd_checks()['complete_human_population_used']


def test_appointed_guardians_keep_event_role_current_duty_and_target_group():
    assert checks.appointment_checks()['native_history_event_and_current_entrustment']


def test_expectation_background_uses_one_forecast_frame_and_guardian_focus():
    assert checks.package_checks()['shared_frame_crowd_and_appointment_descriptions']


def test_closed_contents_quantify_the_same_publics_but_keep_background_separate():
    assert checks.aggregation_checks()['foreground_and_background_independent']


def test_attribution_does_not_execute_the_world_or_expectation_claims():
    assert checks.attribution_checks()['source_claim_and_background_closed']


def test_existing_whole_unit_and_first_sentence_judgments_survive():
    assert checks.structure_checks()['preserved_whole_unit_reviews'] == 13
