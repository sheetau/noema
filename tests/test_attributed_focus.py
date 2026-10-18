from scripts.check_attributed_focus import generic_checks,contrast_checks,native_checks,structure


def test_claim_and_background_attribution_are_independent_of_world_truth():
    assert generic_checks()['attribution_and_world_truth_combinations']==16


def test_scopes_content_roles_and_unknown_attribution_remain_distinct():
    assert contrast_checks()['false_report_does_not_hide_unknown_background']


def test_closed_guardian_and_conditioned_dissemination_reach_the_same_attribution():
    assert native_checks()['all_world_and_expectation_primitives_unknown']


def test_existing_relations_statements_and_review_bindings_are_reused():
    assert structure()['new_semantic_relations']==0
