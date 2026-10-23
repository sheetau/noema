from scripts.review_third_frame_claim import build_report

def test_whole_third_frame_setup_and_display():
    report=build_report()
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':2}
    assert report['source_units']=={'einstein-1905:u0093':426,'einstein-1905:u0094':0}
    assert report['reviewed_math_elements']==12
