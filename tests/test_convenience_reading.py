from scripts.check_convenience_reading import generic_checks, source_checks, ordinary_and_unknown_checks, attribution_checks, integrity_checks


def test_state_goal_and_burden_cannot_be_taken_from_different_methods():
    assert generic_checks()['method_contrasts']['split_state_goal'] == [False, True]


def test_convenience_uses_current_capacity_and_scoped_generalization():
    assert len(source_checks()['contrasts']) == 18


def test_ordinary_capacity_agrees_and_unknown_context_is_not_filled_in():
    assert ordinary_and_unknown_checks()['unknown_inputs_refused'] == 4


def test_attribution_does_not_assert_convenience_or_liking():
    assert attribution_checks()['content_facts_and_liking_not_asserted']


def test_source_scope_and_notations_are_preserved():
    assert integrity_checks()['clause_partition'] == 5
