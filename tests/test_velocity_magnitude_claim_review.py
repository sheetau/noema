from scripts.review_velocity_magnitude_claim import build_report


def test_whole_two_speed_definitions():
    report=build_report()
    assert report['source_units']=={'einstein-1905:u0136':0}
    assert report['reviewed_math_elements']==2
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':1}
