from scripts.check_guardian_reading import generic_checks,scope_checks,source_checks,fact_checks,structure


def test_framing_is_independent_of_world_truth():
    assert len(generic_checks()['combinations'])==24


def test_same_claim_focus_and_additive_order_are_required():
    assert scope_checks()['same_node_multiple_claims_not_conflated']


def test_whole_sentence_presentation_keeps_world_facts_unknown():
    assert len(source_checks()['contrasts'])==16


def test_burden_judgment_and_actual_danger_remain_distinct():
    assert len(fact_checks()['combinations'])==8


def test_complete_sentence_binding_and_existing_reviews_are_preserved():
    assert structure()['exact_focus_subexpression']
