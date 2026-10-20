from scripts import check_fetters_sentence as checks


def test_reference_correction_matches_calls_and_catches_japanese_adjacency():
    assert checks.correction_checks()['japanese_adjacent_reference_regression_checked']


def test_existing_judgments_executable_meanings_and_notations_preserved():
    assert checks.preservation_checks()['roundtrips']


def test_source_partition_and_rebinding_without_automatic_equivalence_claim():
    assert checks.reading_checks()['source_equivalence_is_reviewer_judgment_not_test_result']
