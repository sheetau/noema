from scripts.check_public_civic_opinion import (
    conditional_checks, detail_checks, case_checks, branch_checks, discourse_checks,
    domain_unknown_checks, structure_checks)


def test_public_expression_implies_same_civic_action_noncontravention(): conditional_checks()


def test_all_activities_scholarly_roles_and_audiences_are_included(): detail_checks()


def test_all_levy_cases_keep_the_same_citizen_and_levy(): case_checks()


def test_added_alternative_matches_the_actual_disjunctive_condition(): branch_checks()


def test_attribution_concession_contrast_and_addition_do_not_execute_content(): discourse_checks()


def test_full_domains_and_unknown_inputs_are_not_silently_completed(): domain_unknown_checks()


def test_reading_existing_judgments_and_roundtrips_are_preserved(): structure_checks()
