from scripts.check_insight_threshold import profile_checks,threshold_checks,identity_checks,until_checks,structure_checks


def test_relevant_public_cognition_profile_is_not_item_count_or_alias():
    r=profile_checks();assert r['public_content_inclusion_and_equivalence']['baseline']==[True,False]
    assert not r['only_relevant_corroborated_items']['noise']


def test_insight_crossing_is_nonvacuous_and_not_just_coincident_ability():
    r=threshold_checks();assert sum(r['nonvacuous_same_background_threshold_crossing'].values())==1


def test_same_proposal_background_objects_and_fixed_truth_assessment():
    r=identity_checks();assert not any(r['same_objects_truth_assessment_and_candidate_points'].values())


def test_same_short_period_ends_at_first_sufficient_public_insight():
    r=until_checks();assert sum(r['first_threshold_at_same_bounded_endpoint'].values())==1
    assert r['native_threshold_and_rkh_r5fi_r5fp']


def test_preserved_meanings_reports_and_manuscript():
    r=structure_checks();assert (r['new_definitions'],r['new_primitives'],r['preserved_manuscript_statements'])==(7,2,102)
