from scripts.check_personal_insight_grounds import comparative_checks,content_checks,held_appraisal_checks,grounded_assent_checks,all_parties_checks,structure_checks


def test_strict_epistemic_comparison_preserves_canonical_content_and_scope():
    r=comparative_checks();assert sum(x['value'] for x in r['strict_comparison'])==1
    assert sum(r['canonical_same_domain'].values())==1


def test_same_better_understanding_fits_the_same_new_arrangement():
    r=content_checks();assert sum(r['native_comparison_and_same_configuration_fit'].values())==1
    assert r['exact_binding_cases']==1024 and set(r['one_exact_binding_per_pattern'])=={1}


def test_held_personal_appraisal_does_not_require_objective_truth_or_new_judging():
    r=held_appraisal_checks();assert r['objective_comparison_not_executed']
    assert not any(r['exact_owner_standard_baseline_content'].values())


def test_same_person_uses_that_judgment_for_that_assent_at_that_point():
    r=grounded_assent_checks();assert sum(r['native_same_assent_and_held_reason'].values())==1
    assert r['native_definitions_without_boundaries']


def test_every_fixed_party_can_use_a_different_personal_criterion():
    r=all_parties_checks();assert sum(r['all_fixed_parties_personal_ground'].values())==2


def test_preserved_meanings_reports_and_manuscript():
    r=structure_checks();assert (r['new_definitions'],r['new_primitives'],r['preserved_manuscript_statements'])==(5,5,102)
