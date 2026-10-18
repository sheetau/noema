from scripts.check_relative_dissemination import generic_checks,access_checks,source_checks,unknown_checks,structure


def test_relative_scope_keeps_unreached_members_and_rejects_nonhumans():
    assert generic_checks()['scope_uptake_and_human_combinations']==64


def test_access_is_an_explicit_composed_example_not_a_surroundings_primitive():
    assert access_checks()['human_and_bidirectional_access_combinations']==16


def test_concrete_dissemination_uses_the_same_origin_and_reference_scope():
    assert source_checks()['native_eager_comparisons']==2


def test_unknown_scope_access_and_cause_are_not_false():
    assert unknown_checks()['unknown_inputs_refused']==4


def test_existing_meanings_statements_and_reviews_remain_intact():
    assert structure()['new_primitives']==0
