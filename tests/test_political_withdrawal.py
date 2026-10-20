from scripts import check_political_withdrawal as checks


def test_oppression_binds_its_harm_and_same_excessive_goal():
    assert checks.motive_checks()['desire_excess_and_purpose_must_share_goal_and_actor']


def test_withdrawal_severs_both_prior_ties_through_the_same_target_process():
    assert checks.withdrawal_checks()['declassification_without_withdrawal_refused']


def test_actual_withdrawal_fits_the_existing_causal_possibility_result_slot():
    assert checks.candidate_checks()['native_rqc_result_slot_accepts_closed_rank_zero_function']


def test_existing_statements_and_reviews_are_preserved():
    assert checks.structure_checks()['old_definitions_unchanged']
