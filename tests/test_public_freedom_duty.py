from scripts import check_public_freedom_duty as checks


def test_public_scope_stays_fixed_while_permissions_cover_every_time():
    assert checks.period_checks()['classification_fixed_to_reference']


def test_policy_bindings_and_native_adapter_keep_the_same_public_source_and_period():
    assert len(checks.adapter_checks()['native_adapter']) == 2


def test_duty_does_not_execute_its_policy_and_applies_to_every_public_group():
    assert checks.norm_checks()['actual_permissions_and_temporal_target_unknown_and_unexecuted']


def test_author_attribution_does_not_execute_the_normative_claim():
    assert checks.attribution_checks()['normative_claim_not_executed']


def test_existing_judgments_and_declarations_are_preserved():
    assert checks.structure_checks()['preserved_reviewed_sentence_characters'] == 588
