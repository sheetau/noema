from scripts import check_fifth_sentence_scope as checks


def test_count_and_concession_have_separate_truth_and_negation_scopes():
    assert checks.count_checks()['foreground_negation_preserves_background']


def test_attribution_keeps_source_roles_and_never_evaluates_world_claims():
    assert checks.attribution_checks()['all_world_count_and_expectation_inputs_unexecuted']


def test_prior_judgments_and_declarations_remain_bound_to_the_same_meanings():
    assert checks.structure_checks()['revised_statement_indices'] == [15]
