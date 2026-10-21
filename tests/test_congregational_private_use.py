from scripts.check_congregational_private_use import actual_checks,identity_checks,scope_checks,quotation_checks,structure_checks


def test_actual_congregational_use_and_commission_execution():actual_checks()


def test_same_activity_institution_and_capacity():identity_checks()


def test_all_size_and_occasion_cases_and_actual_inclusion():scope_checks()


def test_quoted_content_is_not_executed():quotation_checks()


def test_unchanged_meanings_primary_evidence_and_roundtrips():structure_checks()
