from scripts import check_modal_prevention as checks


def test_nonpermission_does_not_require_nonperformance():
    assert checks.scope_checks()['unpermitted_but_attempted_countermodel']


def test_cause_attention_and_purpose_target_the_same_normative_result():
    assert checks.binding_checks()['result_attention_and_purpose_share_the_normative_goal']


def test_actual_trial_can_be_unknown_but_required_normative_facts_cannot():
    assert checks.unknown_checks()['actual_trial_courage_success_and_warning_truth_left_unknown']


def test_all_depictions_use_the_revised_claim_and_stage():
    assert checks.attribution_checks()['old_claim_and_old_target_not_silently_reused']


def test_only_the_five_scope_dependent_statements_change():
    assert checks.structure()['revised_statements']==[35,36,47,48,49]
