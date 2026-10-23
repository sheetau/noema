from scripts.review_transverse_ray_claim import build_report

def test_whole_transverse_ray_units_and_evidence():
    r=build_report()
    assert r['whole_units_semantically_verified']
    assert r['verified_full_units']['einstein-1905']==8
    assert r['reviewed_math_elements']==4
