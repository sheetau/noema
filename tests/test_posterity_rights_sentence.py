from scripts.check_posterity_rights_sentence import adoption_checks,qualification_checks,resolution_checks,connection_checks,discourse_checks,structure_checks

def test_same_adopted_decision_occurs_at_the_fixed_formation_point():
    r=adoption_checks();assert sum(r['same_adoption_and_actual_occurrence'].values())==1 and r['unknown_rejected']

def test_lack_of_qualification_and_defiant_grave_infringement_are_separate():
    r=qualification_checks();assert len(r['qualification_and_two_appraisals'])==16 and r['adoption_not_executed']

def test_each_decision_uses_the_same_nature_and_two_appraisals():
    r=resolution_checks();assert sum(r['native_all_decisions_same_nature_and_qualification'].values())==1 and r['no_definition_boundaries']

def test_same_six_targets_and_hypothesis_bind_rights_and_adoption():
    r=connection_checks();assert all(len(m)==36 and sum(m)==6 for m in r['exact_six_position_matrices'].values())
    assert all(sum(t.values())==3 for t in r['conditional_tables'].values())

def test_author_focus_fullness_supplements_and_reason_direction():
    r=discourse_checks();assert sum(r['all_attributions_supplements_focus_fullness_reasons'].values())==1
    assert r['quoted_truth_not_executed'] and r['unknown_rejected']

def test_sentence_integration_preserves_prior_reviews():
    r=structure_checks();assert (r['preserved_statements'],r['added_statements'])==(100,1)
    assert (r['preserved_opening_sentence_characters'],r['new_reviewed_sentence_characters'])==(864,226)
