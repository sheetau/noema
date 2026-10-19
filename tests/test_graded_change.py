from scripts import check_graded_change as checks


def test_graded_change_and_retention_differ_from_binary_acquisition():
    result = checks.generic_checks()
    assert len(result['combinations']) == 64 and len(result['contrasts']) == 33
    assert result['unknown_inputs_refused'] == 8


def test_source_schema_keeps_person_property_reference_and_anchor_fixed():
    result = checks.source_checks()
    assert len(result['contrasts']) == 7 and result['native_current_immaturity_executed']


def test_schema_can_be_quoted_without_asserting_world_truth():
    assert checks.quotation_checks()['world_contents_unknown']


def test_existing_authored_text_and_twelve_reviews_are_unchanged():
    result = checks.structure_checks()
    assert result['new_definitions'] == 5 and result['new_primitives'] == 0
