from scripts.check_epoch_undertakings import period_checks,cohort_checks,party_checks,declaration_checks,formation_checks,integrated_checks,structure_checks

def test_complete_partition_excludes_unassigned_time():
    r=period_checks();assert r['partition_oracle_models']==27
    assert r['uncovered_between_epochs_old_and_new']==[True,False]

def test_cohorts_allow_survivors_and_require_all_members():
    r=cohort_checks();assert r['unknown_rejected']
    assert {n for n,v in r['native_cohort_contrasts'].items() if v}=={'baseline','same_members','disjoint_members'}

def test_actual_parties_are_earlier_members_but_not_whole_cohort():
    r=party_checks();assert r['native_parties_and_formation_anchor']=={'baseline':True,'future_party':False,'late_anchor':False}
    assert r['earlier_nonparty_member_allowed']

def test_oath_and_all_reciprocal_declarations_share_act_terms_and_time():
    r=declaration_checks();assert r['unrealized_terms_and_deity_property_not_executed']
    assert {n for n,v in r['native_same_mutual_act_and_oath'].items() if v}=={'baseline'}

def test_formation_binds_all_parties_to_same_fixed_context():
    r=formation_checks();assert {n for n,v in r['native_rhz_and_exact_dependency_arguments'].items() if v}=={'baseline'}

def test_native_integrated_formation_rejects_missing_or_separate_oath():
    r=integrated_checks();assert r['unknown_rejected'] and r['quotes_not_executed']
    assert {n for n,v in r['all_definitions_native_without_boundaries'].items() if v}=={'baseline'}

def test_dependency_preserves_manuscript_and_pinned_evidence():
    r=structure_checks();assert r['preserved_manuscript_statements']==99
    assert r['new_definitions']==6 and r['new_primitives']==4
