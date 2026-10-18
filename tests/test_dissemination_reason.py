from scripts.check_dissemination_reason import relation_checks,nonfactivity_checks,source_checks,structure


def test_author_reason_direction_and_textual_order():
    assert relation_checks()['full_manuscript_last_statement_evaluated_with_all_content_primitives_unknown']


def test_reason_presentation_is_independent_of_truth_and_actual_freedom():
    assert nonfactivity_checks()['independent_truth_validity_and_actual_freedom_combinations']==16


def test_original_page_and_source_anchors_are_pinned():
    assert source_checks()['exact_connective_range']==[129,133]


def test_previous_statements_meanings_and_reviews_remain():
    assert structure()['total_statements']==33
