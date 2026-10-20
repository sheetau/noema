from scripts.check_clerical_explanation import native_checks,property_checks,binding_checks,scope_checks,discourse_checks,structure_checks


def test_native_same_teaching_and_nonfactive_characterization():native_checks()


def test_same_message_fits_the_appointed_standard():property_checks()


def test_exact_nine_bindings_message_reference_and_conjunction():binding_checks()


def test_all_cases_tasks_activities_and_message_domain():scope_checks()


def test_denn_reason_direction_order_and_attribution():discourse_checks()


def test_preserved_reviews_full_source_coverage_and_roundtrip():structure_checks()
