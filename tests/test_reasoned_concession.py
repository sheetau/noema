from scripts.check_reasoned_concession import generic_checks,order_checks,attribution_checks,native_background_checks,structure


def test_comparison_keeps_the_premise_positive_and_world_truth_independent():
    assert generic_checks()['world_and_comparison_combinations']==64


def test_distinct_discourse_nodes_require_positive_order_without_reverse():
    assert order_checks()['cases']==8


def test_reason_direction_scope_and_background_are_not_interchangeable():
    assert attribution_checks()['attribution_combinations']==64


def test_source_background_compares_the_actual_descriptions_without_executing_them():
    assert native_background_checks()['same_e4_and_gx_on_both_sides']


def test_existing_manuscript_and_nine_reviews_are_preserved():
    assert structure()['nine_review_bindings_preserved']
