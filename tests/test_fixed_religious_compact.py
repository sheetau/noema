from scripts.check_fixed_religious_compact import period_checks,prohibition_checks,terms_checks,execution_checks,agreement_checks,structure_checks

def test_unique_period_and_one_complete_lifetime():
    assert period_checks()['period_and_single_lifetime']['baseline']==[True,True]

def test_every_public_challenge_is_prohibited_without_executing_it():
    assert sum(prohibition_checks()['all_people_all_public_questioning_activities'].values())==1

def test_same_regime_and_prohibition_persist_at_every_interior_point():
    assert sum(terms_checks()['same_configuration_and_prohibition_throughout_period'].values())==1

def test_all_fixed_parties_assent_to_identical_unexecuted_terms():
    assert sum(agreement_checks()['complete_same_terms_assent'].values())==1

def test_prohibited_execution_keeps_person_activity_and_exact_binding():
    assert sum(execution_checks()['actual_execution'].values())==1

def test_pinned_evidence_and_notation_are_preserved():
    assert structure_checks()['main_statements_unchanged']==103
