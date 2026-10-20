from scripts import check_thinking_reform as checks


def test_actual_own_judgment_and_supported_reasons():
    assert checks.reasoning_checks()['native_own_faculty_same_judgment_and_reasons']


def test_fixed_scope_and_assessed_normal_opportunities():
    assert checks.disposition_checks()['all_fixed_topics_and_normal_counterparts']


def test_reform_requires_real_change_and_valid_prior_assessment():
    assert checks.change_checks()['native_full_reform_with_reasoning_and_normality']


def test_both_results_connect_to_the_same_revolutionary_route():
    assert checks.route_checks()['cause_and_result_both_required']


def test_existing_judgments_and_notation_roundtrips():
    assert checks.structure_checks()['old_definitions_unchanged']
