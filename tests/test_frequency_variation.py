from scripts import check_frequency_variation as checks


def test_observed_frequency_and_normality_are_not_interchangeable():
    assert checks.generic_checks()['exceptions_not_erased']


def test_current_deterrence_does_not_entail_unobserved_frequency():
    assert checks.source_checks()['observed_frequency_does_not_entail_frequency_under_variation']


def test_documented_library_and_source_diagnostic_preserve_current_reviews():
    assert checks.structure()['preserved_review_selections']==11
