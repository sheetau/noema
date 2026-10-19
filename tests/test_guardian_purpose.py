from scripts.check_guardian_purpose import purpose_checks, source_checks, attribution_checks, structure


def test_performed_purpose_does_not_execute_or_require_its_goal():
    r = purpose_checks()
    assert len(r['combinations']) == 32 and r['goal_truth_unknown_and_not_executed']


def test_causal_action_and_intended_action_cannot_be_separate():
    r = source_checks()['contrasts']
    assert r['no_goal'][:2] == [False, True]
    assert r['no_event_cause'][:3] == [False, True, True]
    assert r['split_purpose_and_cause'][:3] == [False, True, True]
    assert r['no_judgment'][2:5] == [True, False, False]


def test_attribution_keeps_intent_and_cause_as_unevaluated_content():
    assert attribution_checks()['purpose_and_causation_not_executed']


def test_existing_review_meanings_and_written_roundtrips_are_preserved():
    assert structure()['preserved_review_meanings'] == 11
