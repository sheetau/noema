from scripts.check_compact_causal_denial import causal_checks,adapter_checks,consequence_checks,scope_checks,normative_checks,structure_checks

def test_actual_cause_needs_same_formation_implementation_and_result():
    assert sum(causal_checks()['same_formation_implementation_result_and_actual_cause'].values())==1

def test_exact_object_adapters_fix_assessment_and_agreement_anchor():
    assert len(adapter_checks()['exact_five_objects_and_fixed_context'])==4

def test_conditional_consequence_does_not_execute_world_content():
    assert sum(consequence_checks()['quoted_conditional_consequence'].values())==1

def test_candidate_group_is_complete_without_assent_or_success():
    assert sum(scope_checks()['unformed_candidate_complete_party_group_and_valid_period'].values())==1

def test_universal_prohibition_is_independent_of_effects():
    assert normative_checks()['universal_prohibition_and_causal_consequence_independent']['missing_consequence']==[True,False]

def test_pinned_meanings_and_notations_are_preserved():
    assert structure_checks()['new_primitives']==0
