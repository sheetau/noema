from scripts.review_polygon_clock_claim import build_report

def test_whole_polygon_clock_unit():
    r=build_report()
    assert r['source_units']=={'einstein-1905:u0127':155}
    assert r['reviewed_math_elements']==4
    assert r['verified_full_units']=={'kant-1784':0,'einstein-1905':1}
