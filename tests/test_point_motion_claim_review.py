from scripts.review_point_motion_claim import build_report

def test_whole_point_motion_claim():
    report=build_report()
    assert report['source_units']=={'einstein-1905:u0133':169,'einstein-1905:u0134':0}
    assert report['reviewed_math_elements']==3
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':2}
