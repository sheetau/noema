from scripts.check_focused_dissemination import scalar_checks,native_checks,unknown_checks,future_checks,rank_checks,structure


def test_scalar_background_and_foreground_truth_are_separate():
    assert scalar_checks()['truth_and_ranking_combinations']==16


def test_common_native_dissemination_frame_changes_only_subgroup():
    assert native_checks()['common_closed_arguments']==30


def test_unneeded_unknown_world_or_ranking_is_not_evaluated():
    assert unknown_checks()['unknown_inputs_refused']==4


def test_rank_and_predicate_type_mismatches_are_rejected():
    assert rank_checks()['unsafe_rank_and_wrong_argument_type_refused']==2


def test_whole_future_does_not_assert_initial_condition_or_omit_failures():
    assert future_checks()['initial_condition_not_asserted']


def test_existing_meanings_statements_and_reviews_are_preserved():
    assert structure()['new_primitives']==0
