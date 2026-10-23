from scripts.review_transverse_symmetry_claim import build_report

def test_whole_measured_meaning_symmetry_and_signed_rewrite():
    report=build_report()
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':4}
    assert report['source_units']=={'einstein-1905:u0101':405,'einstein-1905:u0102':0,'einstein-1905:u0103':4,'einstein-1905:u0104':1}
    assert report['reviewed_math_elements']==7
