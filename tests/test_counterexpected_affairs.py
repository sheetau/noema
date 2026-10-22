from scripts import check_counterexpected_affairs as check


def test_nonempty_expectation_and_nonexpectation_scopes():check.expectation_checks()
def test_actual_truth_and_strict_counterexpectation():check.comparison_checks()
def test_exact_almost_all_population_and_small_positive_deficit():check.almost_all_checks()
def test_unfamiliar_framework_fit_is_independent():check.unfamiliar_checks()
def test_native_contextual_aspect_integration():check.context_checks()
def test_adapters_preserve_context_and_supplied_arguments():check.provider_checks()
def test_preserved_meanings_ranks_and_provenance():check.structure_checks()
