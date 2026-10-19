from scripts import check_bound_undertaking as checks


def test_courage_attempt_and_success_are_separate():
    assert len(checks.generic_checks()['combinations'])==32


def test_explicit_adaptation_preserves_unary_undertaking():
    assert len(checks.adapter_checks()['combinations'])==32


def test_four_goal_arguments_and_trial_event_are_preserved():
    assert len(checks.source_checks()['contrasts'])==18


def test_norms_quote_attempts_without_executing_them():
    assert len(checks.norm_checks()['combinations'])==8


def test_preserved_meanings_and_roundtrips():
    assert checks.structure()['active_manuscript_unchanged']
