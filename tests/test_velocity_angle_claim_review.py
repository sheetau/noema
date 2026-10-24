from scripts.review_velocity_angle_claim import build_report


def test_three_whole_units():
    r=build_report()
    assert r['source_units']=={'einstein-1905:u0135':104,'einstein-1905:u0137':3,'einstein-1905:u0138':0}
    assert r['reviewed_math_elements']==1
    assert r['verified_full_units']=={'kant-1784':0,'einstein-1905':3}
