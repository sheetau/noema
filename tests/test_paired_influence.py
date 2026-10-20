from scripts import check_paired_influence as checks


def test_independent_branch_variation_is_not_an_effect_of_the_restriction():
    assert checks.neutral_regression()['neutral_branch_variation_not_counted_as_effect']


def test_matches_cover_every_solution_and_preserve_effect_directions():
    assert checks.matrix_checks()['checked_combinations'] == 96


def test_incomplete_assessment_or_correspondence_is_not_nonhindrance():
    assert checks.guard_checks()['unknown_correspondence_refused']


def test_matched_effects_keep_complete_demands_and_the_same_enlightenment():
    assert checks.alignment_checks()['fixed_public_reference_and_r2ln_goal']


def test_all_four_cases_pass_the_same_rows_worlds_and_ordered_matches():
    assert checks.concrete_checks()['same_all_recipient_rows_and_ordered_matches']


def test_old_meanings_are_preserved_and_the_new_library_roundtrips():
    assert checks.structure_checks()['added_author_statements'] == 0
