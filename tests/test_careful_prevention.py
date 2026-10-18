from scripts.check_careful_prevention import generic_checks,goal_checks,source_checks,attribution_checks,structure


def test_goal_directed_attention_may_be_distributed_without_assuming_success():
    result=generic_checks()
    assert result['combinations']==32 and result['goal_content_unknown']


def test_a_separate_careful_act_cannot_supply_the_causal_act_manner():
    rows=source_checks()['cases']
    assert rows['separate_careful_act']==[False,False,True,True]


def test_goal_adapter_retains_the_same_subject_and_negative_result():
    assert goal_checks()['same_person_and_result_content']


def test_author_attribution_does_not_evaluate_attention_or_purpose():
    assert attribution_checks()['attention_relevance_purpose_and_world_unknown']


def test_existing_reviewed_units_and_other_statements_are_unchanged():
    assert structure()['nine_review_bindings_preserved']
