from scripts import check_use_definitions as check


def test_role_classification_and_shared_references():
    check.classification_checks()


def test_self_definition_and_role_based_remit():
    check.discourse_checks()


def test_reading_preservation_and_roundtrips():
    check.structure_checks()
