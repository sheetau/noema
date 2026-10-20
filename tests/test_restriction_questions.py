from scripts import check_restriction_questions as checks


def test_supplied_example_rows_match_every_original_requirement_and_choice():
    assert checks.row_checks()['all_four_original_demands_and_choices_preserved']


def test_every_candidate_uses_the_same_context_public_and_reference():
    assert checks.binding_checks()['shared_public_reference_and_context']


def test_additional_negative_requirements_use_the_native_comparison():
    assert checks.extra_checks()['additional_negative_requirement_natively_evaluated']


def test_two_questions_allow_more_candidates_and_do_not_assert_an_answer_exists():
    assert checks.question_checks()['fifth_candidate_can_answer']


def test_closed_questions_keep_the_rank_required_by_their_demand_contents():
    assert checks.quotation_checks()['required_outer_quote_rank'] == 2


def test_old_statements_meanings_reviews_and_roundtrips_are_preserved():
    assert checks.structure_checks()['added_author_statements'] == 0
