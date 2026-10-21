from scripts.check_cohort_covenant_denial import importance_checks,supplement_checks,progress_checks,discourse_checks,structure_checks

def test_same_cohort_full_domain_concern_and_high_degree():
    r=importance_checks();assert sum(r['concern_and_high_degree'].values())==1
    assert r['unknown_rejected'] and r['malformed_binding_rejected']

def test_supplement_preserves_main_quantifier_scope():
    r=supplement_checks();assert len(r['same_scope_supplement_oracle'])==16 and r['importance_does_not_filter_main_scope']

def test_progress_summary_keeps_same_group_and_temporal_arguments():
    r=progress_checks();assert r['same_three_kinds_as_inability']['baseline']==[True]*3
    assert r['same_three_kinds_as_inability']['wrong_assessment']==[False,False,True]

def test_scoped_parenthesis_focus_summary_and_negative_presentation():
    r=discourse_checks();assert sum(r['scoped_presentation_and_closed_quotes'].values())==1
    assert r['quoted_truth_not_executed'] and r['unknown_rejected']

def test_sentence_integration_preserves_prior_reviews():
    r=structure_checks();assert r['preserved_statements']==99 and r['added_statements']==1
    assert r['preserved_opening_sentence_characters']==614 and r['new_reviewed_sentence_characters']==250
