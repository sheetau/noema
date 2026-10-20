from scripts import check_reversal_yoke as checks


def test_yoke_state_uses_the_existing_bodily_description():
    assert checks.depiction_checks()['native_neck_frame_attachment_and_traction_relation']


def test_state_substitution_preserves_case_condition_and_time():
    assert checks.generalized_checks()['original_temporal_and_conditional_body_exactly_preserved']


def test_depiction_and_target_bind_the_same_public_and_case():
    assert checks.family_checks()['same_public_case_and_reference_in_all_families']


def test_kind_anaphora_and_nonliteral_attribution_do_not_assert_world_facts():
    assert checks.attribution_checks()['all_world_inputs_unknown_without_execution']


def test_existing_reviews_and_prior_yoke_meanings_survive():
    assert checks.structure_checks()['prior_yoke_state_dependencies_checked']
