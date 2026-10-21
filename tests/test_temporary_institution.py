from scripts.check_temporary_institution import period_checks,introduction_checks,continuity_checks,milestone_checks,structure_checks

def test_shortness_determination_and_valid_nonzero_period_are_separate():
    r=period_checks();assert r['ordered_nonzero_bounded_term']['unspecified']==[True,False]
    assert r['ordered_nonzero_bounded_term']['long']==[True,False]
    assert len(r['determination_and_shortness_independent'])==4

def test_same_actual_law_adoption_introduces_the_same_religious_arrangement():
    r=introduction_checks();assert sum(r['native_law_and_same_introduction'].values())==2
    assert not any(r['all_six_introduction_positions']) and r['no_definition_boundaries']

def test_every_interior_point_has_both_same_institution_and_public_freedom():
    r=continuity_checks();assert len(r['three_points_order_and_freedom'])==64
    assert sum(x['value'] for x in r['three_points_order_and_freedom'])==1
    assert not any(r['same_frame'].values()) and r['half_open_interval']

def test_first_milestone_matches_same_short_term_without_forcing_later_abolition():
    r=milestone_checks();rows=r['first_milestone_at_same_determined_end']
    assert len(rows)==16 and sum(x['values'][1] for x in rows)==1
    assert all(x['values'][0] for x in rows) and r['endpoint_and_later_continuation_allowed']

def test_imports_prior_evidence_and_main_manuscript_remain_unchanged():
    r=structure_checks();assert (r['new_definitions'],r['new_primitives'],r['preserved_manuscript_statements'])==(6,3,102)
