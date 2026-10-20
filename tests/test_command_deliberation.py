from scripts.check_command_deliberation import (
    profile_checks,appraisal_checks,discussion_checks,bound_checks,unknown_checks,structure_checks)


def test_signed_command_content_and_causal_improvement():
    profile_checks()


def test_purpose_and_utility_are_separate_criteria():
    appraisal_checks()


def test_intended_audible_discussion_in_service():
    discussion_checks()


def test_same_officer_command_and_discussed_content():
    bound_checks()


def test_unknown_inputs_are_not_negated_facts():
    unknown_checks()


def test_preserved_meanings_and_notation():
    structure_checks()
