from scripts.check_method_scope import combinations,scope_checks,source_checks,structure


def test_scoped_ability_uses_only_available_methods_in_the_declared_scope():
    assert combinations()['count']==64


def test_scope_preserves_outcome_failures_and_does_not_fill_unknowns():
    assert scope_checks()['unknown_inputs_refused']==4


def test_training_route_is_not_a_witness_for_an_execution_only_scope():
    assert source_checks()['cases']['training_route_only_succeeds']==[True,False,False,True,True,False,True]


def test_generic_restriction_adds_no_primitive_and_preserves_notations():
    assert structure()['new_generic_primitives']==0
