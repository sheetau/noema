from scripts.check_benevolent_framing import action_checks,frame_checks,source_checks,presentation_checks,structure


def test_goodwill_and_action_do_not_require_actual_benefit():
    assert len(action_checks()['combinations'])==48


def test_critical_framing_is_distinct_from_sincere_praise_and_factual_truth():
    r=frame_checks()
    assert r['quoted_world_facts_unknown'] and r['same_node_multiple_claims_not_conflated']


def test_favorable_evaluation_uses_the_same_assumption_and_beneficiary():
    assert source_checks()['same_assumption_witness_executed']


def test_source_presentation_does_not_assert_kindness_or_its_opposite():
    assert presentation_checks()['positive_evaluation_and_its_negation_not_asserted']


def test_event_refactor_expands_exactly_and_preserves_previous_reviews():
    assert structure()['refactor_expansion_exact']
