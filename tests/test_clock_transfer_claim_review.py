from scripts.review_clock_transfer_claim import build_report

def test_whole_clock_transfer_unit():
    r=build_report()
    assert r['source_units']=={'einstein-1905:u0126':424}
    assert r['reviewed_math_elements']==14
    assert r['verified_full_units']=={'kant-1784':0,'einstein-1905':1}
