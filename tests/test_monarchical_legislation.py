from scripts.check_monarchical_legislation import enactment_checks,prohibition_checks,limit_checks,will_checks,ground_checks,standing_checks,foundation_checks,structure_checks

def test_monarch_holds_office_at_the_same_adoption_point():
    assert enactment_checks()['monarch_and_enactment_same_point']['split_points']==[True,False]

def test_nonpermission_uses_explicit_negative_requirements():
    assert not prohibition_checks()['explicit_negative_requirements']['r5md']['absent']

def test_same_people_law_and_candidate_are_kept_for_every_monarch():
    assert not limit_checks()['all_monarchs_same_people_law_and_candidate']['missing_second_monarch_ban']

def test_entire_public_will_requires_both_content_and_incorporation():
    assert not will_checks()['native_complete_public_range_and_structural_incorporation']['own_extra_law']

def test_grounding_does_not_execute_quoted_authority_or_will():
    assert ground_checks()['ground_and_authority_not_executed']

def test_institutional_monarch_scope_does_not_presuppose_justified_authority():
    assert standing_checks()['native_scope_and_separate_authority_content']['no_authority']==[True,False]

def test_authority_requires_incorporation_without_converse_entitlement():
    assert foundation_checks()['grounding_and_necessary_but_not_sufficient_incorporation']['incorporation_without_authority']

def test_prior_main_text_and_evidence_are_preserved():
    assert structure_checks()['preserved_main_statements']==105
