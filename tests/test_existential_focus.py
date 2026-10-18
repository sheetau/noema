from scripts.check_existential_focus import conditional_checks,native_background_checks,separation_checks,structure


def test_conditional_focus_uses_the_same_candidate_and_origin():
    assert conditional_checks()['condition_content_comparison_combinations']==32


def test_native_existential_background_does_not_execute_the_world():
    assert native_background_checks()['common_existential_arguments']==22


def test_foreground_and_comparison_metadata_remain_independent():
    assert separation_checks()['selected_unknowns_refused']==4


def test_branch_providers_route_scope_and_existing_reviews_are_preserved():
    assert structure()['same_branch_supplied_to_all_22_fields']
