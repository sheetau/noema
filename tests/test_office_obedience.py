from scripts.check_office_obedience import (
    obedience_checks, permission_checks, requirement_checks,
    adapter_checks, scope_checks, discourse_checks, structure_checks)


def test_job_scoped_guided_obedience_and_full_domain_refusal():
    obedience_checks()


def test_permission_denial_in_the_same_office_work():
    permission_checks()


def test_quoted_requirement_keeps_reference_and_does_not_execute():
    requirement_checks()


def test_exact_bindings_and_explicit_reference_adapter():
    adapter_checks()


def test_fixed_anaphoric_scope_and_two_modalities():
    scope_checks()


def test_correction_acknowledgment_and_explanation():
    discourse_checks()


def test_source_reading_and_preserved_judgments():
    structure_checks()
