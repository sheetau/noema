from scripts.check_personal_endorsement_case import (
    supposition_checks,composition_checks,reference_checks,quotation_checks,structure_checks)


def test_constructed_personal_supposition_and_nonempty_hypothetical_scope():supposition_checks()


def test_same_doctrine_in_personal_judgment_and_responsible_exposition():composition_checks()


def test_same_person_names_reference_and_unknown_input_rejection():reference_checks()


def test_quotation_does_not_execute_the_case():quotation_checks()


def test_unchanged_imports_roundtrips_and_prior_evidence():structure_checks()
