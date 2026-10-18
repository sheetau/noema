from scripts.check_preparation_course import combinations,contrasts,source_checks,structure


def test_capacity_changes_require_assessment_of_intermediate_states():
    assert combinations()['count']==64


def test_missing_learning_evidence_is_not_proof_that_no_capacity_was_acquired():
    assert contrasts()['unknown_inputs_refused']==5


def test_method_scope_is_composed_and_unclassified_methods_do_not_prove_inability():
    assert source_checks()['cases']['missing_middle']==[False,False,True,False,True,False,False,False]


def test_existing_acquisition_definitions_are_reused_with_all_notations():
    assert structure()['original_acquisition_and_interval_bodies_preserved']
