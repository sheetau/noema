from scripts.check_scholarly_self_ascription import (
    membership_checks, self_checks, writing_checks, context_checks, structure_checks)


def test_membership_contents_and_exact_bindings():
    membership_checks()


def test_first_person_ascription_is_not_truth():
    self_checks()


def test_native_written_public_address():
    writing_checks()


def test_same_office_member_in_scholarly_role():
    context_checks()


def test_standalone_library_and_preserved_meanings():
    structure_checks()
