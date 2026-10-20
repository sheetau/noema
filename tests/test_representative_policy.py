from scripts.check_representative_policy import period_checks,coverage_checks,binding_checks,appointment_checks,structure_checks


def test_full_period_policy_and_extra_nonrepresentative_expositions():period_checks()


def test_all_tasks_and_original_recipient_coverage():coverage_checks()


def test_exact_nine_binding_adapter():binding_checks()


def test_same_past_appointment_and_distinct_current_office():appointment_checks()


def test_preserved_meanings_evidence_and_quote_rank():structure_checks()
