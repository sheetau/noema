from scripts.check_judgment_standards import (
    evidence_checks, binding_checks, judgment_checks, construction_checks, ability_checks, structure,
)


def test_missing_conflicting_and_negative_evidence_remain_distinct():
    assert evidence_checks()['combinations'] == 64


def test_standard_context_and_performance_point_remain_separate():
    assert len(binding_checks()['foreign_bindings']) == 18


def test_all_items_use_one_owned_resource_and_one_judgment():
    assert judgment_checks()['split_resource_evidence_rejected']


def test_closed_criterion_preserves_references_without_evaluating_evidence():
    assert construction_checks()['five_references_retained']


def test_documented_conformity_is_an_executable_ability_goal():
    assert ability_checks()['native_judgment_and_task_indexed_ability_executed']


def test_existing_text_and_reviewed_meanings_are_preserved():
    assert structure()['preserved_review_selections'] == 10
