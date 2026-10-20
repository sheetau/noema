from scripts.check_civic_example import (
    refusal_checks,conditional_checks,detail_checks,quantifier_checks,whole_checks,
    focus_checks,discourse_checks,unknown_checks,structure_checks)


def test_all_candidate_responses_prohibited_under_same_normative_source():
    refusal_checks()


def test_same_levy_criticism_standard_and_conditional_consequences():
    conditional_checks()


def test_all_four_criticism_fields():
    detail_checks()


def test_all_eight_levy_fields_and_independent_refusal_clause():
    quantifier_checks()


def test_all_three_contents_share_evaluation_point():
    whole_checks()


def test_sogar_has_strict_expectation_background_without_truth_export():
    focus_checks()


def test_attribution_aside_assessment_focus_and_order():
    discourse_checks()


def test_unknown_inputs_are_rejected():
    unknown_checks()


def test_preserved_statements_reviews_meanings_source_and_notation():
    structure_checks()
