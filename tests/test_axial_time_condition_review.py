from scripts.review_axial_time_condition import build_report,records

def test_hypothetical_trial_and_displayed_equation_share_necessary_conclusion():
    report=build_report()
    assert report['source_units']=={'einstein-1905:u0049':167,'einstein-1905:u0050':0}
    assert report['verified_full_units']['einstein-1905']==2
    assert report['reviewed_math_elements']==7
    assert not report['general_physical_derivation_proved']
    first,second=records()
    assert first['selection']['statements'][-1]==second['selection']['statements'][0]
