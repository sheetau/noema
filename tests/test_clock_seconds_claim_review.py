from scripts.review_clock_seconds_claim import build_report

def test_whole_clock_seconds_claim():
    report=build_report()
    assert set(report['source_units'])=={'einstein-1905:u0125'}
    assert report['reviewed_math_elements']==2
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':1}
