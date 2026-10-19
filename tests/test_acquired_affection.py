from scripts import check_acquired_affection as checks


def test_affection_disposition_is_independent_of_current_feeling_and_acceptance():
    result = checks.disposition_checks()
    assert len(result['combinations']) == 32 and len(result['contrasts']) == 8
    assert result['unknown_inputs_refused'] == 3


def test_acquisition_requires_same_person_process_history_and_persistence():
    result = checks.acquisition_checks()
    assert len(result['contrasts']) == 19 and result['unknown_inputs_refused'] == 9


def test_acquired_affection_can_be_quoted_without_asserting_world_truth():
    assert checks.quotation_checks()['world_contents_unknown']


def test_twelve_reviewed_units_and_all_existing_assertions_are_unchanged():
    result = checks.structure_checks()
    assert result['preserved_review_selections'] == 12 and result['new_authored_assertions'] == 0
