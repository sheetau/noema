from scripts import check_public_slow_attainment as checks


def test_only_slow_requires_attainment_and_excludes_every_faster_route():
    result = checks.route_checks()
    assert result['faster_second_process_in_same_candidate_refused']
    assert result['no_attainment_is_not_only_slow']


def test_old_goal_and_new_route_share_time_population_and_extent():
    assert checks.witness_checks()['old_hzng_goal_and_explicit_route_agree']


def test_fourth_sentence_and_inference_are_nonfactive_attributions():
    assert checks.attribution_checks()['all_world_inputs_unknown_without_execution']


def test_fourth_sentence_review_preserves_prior_meanings_and_judgments():
    assert checks.structure_checks()['old_definitions_unchanged']
