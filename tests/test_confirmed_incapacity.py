from scripts import check_confirmed_incapacity as checks


def test_native_current_incapacity_focus():
    assert checks.capacity_checks()['native_current_capacity_definitions_executed']


def test_assurance_scope_and_attribution():
    assert checks.discourse_checks()['assurance_focus_only_current_incapacity']


def test_preserved_components_and_first_sentence():
    assert checks.reused_checks()['first_sentence_review_preserved']


def test_sentence_reading_and_roundtrips():
    assert checks.structure_checks()['reviewed_second_sentence_characters'] == 139
