from scripts import check_defeasible_learning as checks


def test_plausible_future_keeps_unsuccessful_hypotheses_and_checks_all_times():
    assert checks.generic_checks()['failed_hypotheses_retained']


def test_native_intellectual_and_bodily_learning_have_independent_outcomes():
    assert checks.native_checks()['native_capacity_experience_contribution_and_acquisition_executed']


def test_revised_learning_is_a_reason_and_a_depiction_without_world_assertion():
    assert checks.attribution_checks()['world_contents_unknown']


def test_removing_superseded_depiction_preserves_reviewed_meanings_and_notations():
    assert checks.structure()['review_bindings_reindexed_without_meaning_change']
