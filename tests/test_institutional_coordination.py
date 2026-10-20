from scripts.check_institutional_coordination import (
    alternatives_checks, binding_checks, structure_checks)


def test_shared_participants_and_inclusive_alternatives():
    alternatives_checks()


def test_shared_references_requirements_and_unknown_inputs():
    binding_checks()


def test_native_library_and_preserved_evidence():
    structure_checks()
