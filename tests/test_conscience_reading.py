from scripts.check_conscience_reading import (
    task_checks, independence_checks, substitution_checks, integrity_checks,
)


def test_self_assessment_uses_the_same_actor_judgment_and_scene():
    assert len(task_checks()['same_judgment_combinations']) == 64


def test_substituted_assessment_does_not_assert_self_performance():
    assert independence_checks()['unknown_self_assessment_does_not_prevent_quoted_supply']


def test_substitution_binds_provider_beneficiary_task_and_scene():
    assert substitution_checks()['self_assessment_content_never_executed']


def test_source_reading_is_pinned_without_changing_the_manuscript():
    assert integrity_checks()['current_definitions_unchanged']
