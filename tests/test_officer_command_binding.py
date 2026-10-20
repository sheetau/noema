from scripts.check_officer_command_binding import (
    message_checks, officer_checks, hierarchy_checks, delivery_checks, bound_checks, structure_checks)


def test_signed_same_person_command_content():
    message_checks()


def test_same_officer_role_and_institution():
    officer_checks()


def test_same_institution_strict_rank_order():
    hierarchy_checks()


def test_addressed_command_is_not_its_fulfillment():
    delivery_checks()


def test_bound_officer_superior_and_command():
    bound_checks()


def test_meanings_evidence_and_roundtrips():
    structure_checks()
