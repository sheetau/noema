from scripts.review_longitudinal_elimination import build_report

def test_four_complete_source_readings():
    report=build_report()
    assert report['whole_units_semantically_verified']
    assert report['verified_full_units']['einstein-1905']==4
    assert report['reviewed_math_elements']==6
