from scripts import check_current_deprivation as checks


def test_current_self_use_capacity_is_neither_current_opportunity_nor_unguided_use():
    result = checks.capacity_checks()
    assert len(result['combinations']) == 16 and len(result['contrasts']) == 9
    assert result['unknown_inputs_refused'] == 7


def test_permission_history_current_inability_cause_adoption_and_attempt_are_independent():
    result = checks.causal_checks()
    assert len(result['independent_conditions']) == 32 and len(result['contrasts']) == 14
    assert result['unknown_inputs_refused'] == 5


def test_quotation_preserves_unknown_world_contents():
    assert checks.quotation_checks()['world_contents_unknown']


def test_existing_authored_text_and_twelve_review_bindings_are_unchanged():
    result = checks.structure_checks()
    assert result['preserved_review_selections'] == 12 and result['new_authored_assertions'] == 0
