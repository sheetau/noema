from scripts.check_courageous_undertaking import generic_checks,source_checks,attribution_checks,structure,alignment


def test_undertaking_requires_same_actor_goal_event_and_courage_but_not_success():
    assert generic_checks()['courage_attempt_actor_occurrence_success_combinations']==32


def test_practical_latin_and_motto_do_not_fall_back_to_old_courage_only_content():
    assert source_checks()['motto_uses_updated_latin_and_unchanged_german']


def test_quotation_does_not_assert_courage_undertaking_or_goal_success():
    assert attribution_checks()['all_quoted_world_relations_unknown']


def test_eight_reviewed_units_keep_their_exact_dependencies():
    assert structure()['eight_review_bindings_preserved']


def test_partial_candidate_is_not_whole_paragraph_equivalence():
    assert alignment()['full_semantic_equivalence'] is False
