from scripts.review_reciprocal_claim import build_report

def test_whole_rest_identity_and_reciprocal_formula():
    report=build_report()
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':2}
    assert report['source_units']=={'einstein-1905:u0095':167,'einstein-1905:u0096':1}
    assert report['reviewed_math_elements']==8
