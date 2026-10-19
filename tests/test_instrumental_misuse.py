from scripts import check_instrumental_misuse as checks


def test_use_and_its_own_examination():
    assert checks.generic_checks()['irrelevant_judgment_not_counted']


def test_same_subject_faculty_activity_and_cause():
    assert checks.binding_checks()['split_activities_refused']


def test_native_persistence_and_capacity():
    assert checks.native_checks()['native_h26_and_current_capacity_executed']


def test_metaphor_and_finite_evaluation_limit():
    assert checks.presentation_checks()['whole_category_evaluation_explicitly_refused']


def test_existing_reviews_and_components():
    assert checks.reused_checks()['preserved_reviewed_sentence_characters'] == 247


def test_source_and_roundtrips():
    assert checks.structure_checks()['roundtrips']
