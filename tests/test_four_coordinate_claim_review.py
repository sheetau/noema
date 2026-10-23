from scripts.review_four_coordinate_claim import build_report

def test_whole_four_coordinate_units_and_evidence():
    r=build_report()
    assert r['whole_units_semantically_verified']
    assert r['verified_full_units']['einstein-1905']==4
    assert r['reviewed_math_elements']==3
