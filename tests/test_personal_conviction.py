from scripts.check_personal_conviction import conviction_checks,modal_checks,reference_checks,quotation_checks,structure_checks


def test_personal_affirmation_and_full_conviction():conviction_checks()


def test_nonvacuous_hypothetical_negation_scope():modal_checks()


def test_same_content_judgment_reference_and_unknown_rejection():reference_checks()


def test_closed_hypothetical_quotation():quotation_checks()


def test_preserved_meanings_and_pinned_reading_evidence():structure_checks()
