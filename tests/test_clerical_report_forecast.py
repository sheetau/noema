from scripts.check_clerical_report_forecast import native_checks,binding_checks,forecast_checks,case_checks,discourse_checks,structure_checks


def test_native_pair_pointed_reasons_and_fixed_audiences():native_checks()


def test_same_bindings_and_unspecified_message_witnesses():binding_checks()


def test_nonempty_future_candidates_and_de_dicto_contents():forecast_checks()


def test_all_clerical_cases_use_same_forecast():case_checks()


def test_author_attribution_and_example_direction():discourse_checks()


def test_reading_prior_reviews_and_roundtrip():structure_checks()
