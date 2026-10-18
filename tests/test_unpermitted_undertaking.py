from scripts.check_unpermitted_undertaking import norm_checks,binding_checks,source_checks,attribution_checks,structure


def test_missing_permission_does_not_collapse_prohibition_undertaking_or_success():
    assert norm_checks()['combinations']==32


def test_quoted_goal_and_single_person_binding_are_retained():
    assert binding_checks()['closed_goal_preserved']


def test_permission_is_checked_at_the_same_prior_time_for_all_selected_recipients():
    rows=source_checks()['cases']
    assert rows['allowed_other_recipient']==[False,True,True,True]
    assert rows['allowed_only_now']==[True,True,True,True]


def test_both_updated_attributions_keep_world_and_norms_unevaluated():
    assert attribution_checks()['all_world_and_normative_inputs_unknown']


def test_only_the_two_unreviewed_clause_statements_change():
    assert structure()['changed_statement_indices']==[35,36]
