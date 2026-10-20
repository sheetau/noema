from scripts.check_clerical_conscience import native_checks,arrangement_checks,scope_checks,discourse_checks,structure_checks


def test_actual_scoped_imputation_and_unknown_inputs():native_checks()


def test_both_prior_roles_and_exact_ten_place_arrangement():arrangement_checks()


def test_all_prior_cases_keep_their_person_roles_and_referents():scope_checks()


def test_addition_attribution_order_and_nonfactivity():discourse_checks()


def test_inherited_reviews_source_coverage_and_roundtrips():structure_checks()
