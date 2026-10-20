from scripts.check_scholarly_compatibility import (
    premise_checks, result_checks, binding_checks, quantifier_checks, focus_checks, discourse_checks, structure_checks)


def test_conditional_premise_without_existing_publication():
    premise_checks()


def test_possible_execution_with_record_and_no_work_impairment():
    result_checks()


def test_same_method_and_source_provider_bindings():
    binding_checks()


def test_conditional_scope_and_independent_arguments():
    quantifier_checks()


def test_self_ascription_focus():
    focus_checks()


def test_conditional_nonfactive_discourse():
    discourse_checks()


def test_preserved_meanings_reviews_and_roundtrips():
    structure_checks()
