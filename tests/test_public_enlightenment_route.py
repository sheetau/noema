from scripts import check_public_enlightenment_route as checks


def test_attainment_episodes_match_the_same_existing_enlightenment_goal():
    assert checks.episode_checks()['separate_processes_not_merged']


def test_public_use_is_productive_in_the_same_process_not_merely_present():
    assert checks.part_checks()['native_public_use_classification']


def test_possibility_and_exclusion_cover_all_candidates_and_processes():
    assert checks.quantifier_checks()['independently_enumerated_goal_and_public_part_combinations'] == 256


def test_native_goal_and_public_classification_connect_to_the_quantifiers():
    assert checks.combined_checks()['native_goal_ratio_period_public_classification_and_quantification']


def test_authored_claim_preserves_scope_without_executing_quoted_contents():
    assert checks.claim_checks()['quoted_claim_not_executed']


def test_old_statements_and_readings_are_preserved():
    assert checks.structure_checks()['preserved_reviewed_sentence_characters'] == 588
