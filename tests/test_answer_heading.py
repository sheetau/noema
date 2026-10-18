from scripts.check_answer_heading import generic_checks,source_checks,structure,alignment


def test_heading_requires_occurrence_containment_answer_role_and_forward_reference():
    assert generic_checks()['presentation_containment_response_order_and_distinctness_combinations']==32


def test_old_opening_and_footnote_do_not_replace_the_title_framing():
    assert source_checks()['opening_and_footnote_cannot_replace_heading']


def test_heading_addition_preserves_meanings_names_and_review_bindings():
    assert structure()['seven_review_bindings_preserved']


def test_formal_report_registers_only_draft_coverage_before_separate_review():
    assert alignment()['full_semantic_equivalence'] is False
