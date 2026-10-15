from scripts import check_material_mass_extension as check


def test_every_selected_point_and_case_must_satisfy_the_same_law():
    rows=check.scope_checks()['cases'][check.CORE]
    assert rows['baseline']==[True,True]
    assert rows['valid_second_event']==[True,True]
    assert rows['bad_second']==rows['bad_second_event']==[True,False]
    assert rows['unselected_bad']==[True,True]


def test_reported_reason_does_not_prove_the_physical_transfer():
    report=check.attribution_check()
    assert report['quoted_targets']==[['claim','sera'],['reason','seqw','sera']]
    assert not report['mass_law_derived_from_charge_capability']
