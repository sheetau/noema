from scripts import check_qualitative_influence as checks


def test_native_intervention_solutions_allow_ties_and_separate_mixed_effects():
    assert checks.mechanism_checks()['exhaustive_mechanism_grade_combinations'] == 256


def test_nonhindrance_requires_valid_assessed_comparable_results():
    assert checks.guard_checks()['missing_or_invalid_evidence_not_nonhindrance']


def test_questions_keep_scope_and_same_candidate_without_forcing_answers():
    assert checks.question_checks()['answer_sets'] == [['harm', 'mixed'], ['help']]


def test_library_preserves_imports_without_claiming_source_completion():
    assert checks.structure_checks()['new_semantically_reviewed_characters'] == 0
