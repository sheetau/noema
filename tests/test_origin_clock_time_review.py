from scripts.review_origin_clock_time import build_report

def test_whole_origin_clock_time():
    report=build_report()
    assert set(report['source_units'])=={'einstein-1905:u0123','einstein-1905:u0124'}
    assert report['reviewed_math_elements']==1
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':2}
