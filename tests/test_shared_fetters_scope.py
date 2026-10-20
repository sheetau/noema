from scripts import check_shared_fetters_scope as checks

def test_role_image_is_inside_fixed_reference_range():
    assert checks.generic_checks()['combinations']==64

def test_same_antecedent_people_and_presentation_context():
    assert checks.scope_checks()['presentation_context_not_use_time']

def test_outsider_is_rejected_without_filtering_the_case():
    assert checks.binding_checks()['old_candidate_accepts_outsider_counterexample']

def test_native_conditional_generic_with_person_scope():
    assert checks.native_checks()['native_generic_capacity_cause_and_continuation_executed']

def test_assertion_and_depiction_use_the_new_shared_scope():
    assert checks.presentation_checks()['world_contents_not_executed_by_attribution']

def test_preserved_judgments_and_reversible_notations():
    assert checks.structure_checks()['roundtrips']
