from scripts import check_reversal_focus as checks


def test_focus_extracts_the_same_conditional_and_antecedent_property():
    assert checks.attachment_checks()['conditional_projection_exact_after_supply_and_alpha_normalization']


def test_public_self_coercion_preserves_the_condition_and_all_targets():
    assert checks.conditional_checks()['no_unconditional_coercion']


def test_scope_binds_three_roles_without_selecting_successes():
    assert checks.family_checks()['scopes_not_filtered_by_success']


def test_focus_attribution_does_not_execute_the_world_claim():
    assert checks.attribution_checks()['all_world_inputs_unknown_without_execution']


def test_old_meanings_and_reviews_are_preserved():
    assert checks.structure_checks()['inherited_meanings_unchanged']
