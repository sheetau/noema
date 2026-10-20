from scripts.check_civic_noncontravention import (
    target_checks, finite_scope_checks, domain_checks, quotation_checks, unknown_checks, structure_checks)


def test_each_required_polarity_matches_the_same_target_and_bindings():
    target_checks()


def test_three_requirement_forms_and_explicit_action_scope_diagnostics():
    finite_scope_checks()


def test_finite_evaluation_refuses_full_description_domains():
    domain_checks()


def test_ranked_quotation_preserves_conformity_without_executing_it():
    quotation_checks()


def test_unknown_requirements_scopes_and_truth_are_rejected():
    unknown_checks()


def test_existing_meanings_and_both_notations_are_preserved():
    structure_checks()
