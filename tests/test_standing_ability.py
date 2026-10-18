from scripts.check_standing_ability import combinations,profile_checks,source_checks,structure


def test_ability_profile_does_not_require_a_current_opportunity():
    assert combinations()['count']==16


def test_bad_profiles_unknowns_and_partial_failures_are_not_inability():
    assert profile_checks()['unknown_inputs_refused']==7


def test_current_source_condition_can_differ_from_fixed_person_profile():
    rows=source_checks()['cases']
    assert rows['blocked_now_but_capable_with_opportunity']==[False,True,True,False,True,False]


def test_generic_construction_does_not_silently_change_authored_kant():
    assert structure()['new_generic_primitives']==0
