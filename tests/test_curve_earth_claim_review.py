from scripts.review_curve_earth_claim import build_report

def test_whole_curve_earth_clock_unit():
    r=build_report()
    assert r['source_units']=={'einstein-1905:u0128':552}
    assert r['reviewed_math_elements']==5
    assert r['verified_full_units']=={'kant-1784':0,'einstein-1905':1}
