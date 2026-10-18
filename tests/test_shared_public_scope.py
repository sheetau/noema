from scripts.check_shared_public_scope import scope_checks,connection_checks,attribution_checks,structure


def test_public_membership_keeps_the_same_reference_across_opportunities():
    assert scope_checks()['public_reference_person_and_opportunity_combinations']==36


def test_permission_and_future_qualification_share_the_public_scope():
    assert connection_checks()['membership_qualification_permission_combinations']==64


def test_attribution_keeps_the_guardian_group_distinct():
    assert attribution_checks()['guardian_governed_group_kept_separate']


def test_derived_population_preserves_existing_meanings_and_reviews():
    assert structure()['permission_and_membership_use_identical_public_and_reference']
