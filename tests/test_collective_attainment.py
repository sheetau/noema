from scripts.check_collective_attainment import truth_checks,scope_checks,message_checks,source_checks,structure


def test_collective_attainment_does_not_require_unanimity():
    assert truth_checks()['combinations']==128


def test_missing_assessment_or_wrong_population_is_not_nonattainment():
    assert scope_checks()['unknown_inputs_refused']==9


def test_question_and_answer_preserve_their_content_and_force():
    assert message_checks()['force_distinct_from_content']


def test_existing_capacity_definitions_feed_both_population_criteria():
    assert source_checks()['native_fo_up_h4l_executed']


def test_comparison_preserves_manuscript_and_all_ten_reviewed_selections():
    assert structure()['preserved_review_selections']==10
