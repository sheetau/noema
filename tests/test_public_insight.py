from scripts.check_public_insight import scope_checks,grounding_checks,corroboration_checks,connection_checks,native_insight_checks,progress_checks,structure_checks

def test_same_institution_field_and_canonical_item():
    r=scope_checks();assert sum(r['all_same_subject_relations'].values())==1 and r['canonical_alias_preserved']

def test_exact_public_judgment_and_its_current_ground():
    r=grounding_checks();assert len(r['seven_conditions'])==128
    assert sum(x['value'] for x in r['seven_conditions'])==1 and not any(r['exact_public_judgment_and_ground'].values())

def test_corroboration_is_positive_and_uses_public_evidence_for_same_content():
    r=corroboration_checks();assert len(r['six_conditions'])==64
    assert sum(x['value'] for x in r['six_conditions'])==1 and not any(r['same_content_confirmed_with_public_evidence'].values())

def test_same_grounding_judgment_is_corroborated_with_nonempty_witnesses():
    r=connection_checks();assert len(r['same_nonempty_grounding_and_confirmation_witnesses'])==16
    assert r['different_judgment_confirmation_rejected']

def test_native_cognition_and_public_confirmation_cannot_replace_one_another():
    r=native_insight_checks();assert sum(r['native_cognition_publicity_and_corroboration'].values())==1
    assert r['no_definition_boundaries']

def test_public_gain_not_alias_or_same_level_replacement_or_unanimity():
    r=progress_checks();assert sum(r['public_insight_gain_without_unanimity'].values())==2
    assert r['does_not_assert_proposal_sufficiency']

def test_preserved_meanings_reports_and_manuscript():
    r=structure_checks();assert (r['new_definitions'],r['new_primitives'],r['preserved_manuscript_statements'])==(6,4,102)
