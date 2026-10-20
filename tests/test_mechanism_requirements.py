from scripts.check_mechanism_requirements import (
    passive_checks, requirements_checks, attribution_checks, structure_checks)


def test_role_scoped_passivity_and_exact_adapter():
    passive_checks()


def test_same_required_means_and_unexecuted_role_content():
    requirements_checks()


def test_partial_attribution_does_not_execute_its_content():
    attribution_checks()


def test_registered_judgments_and_native_roundtrips():
    structure_checks()
