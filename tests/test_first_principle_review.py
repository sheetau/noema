from scripts.review_first_principle import build_report

def test_whole_unit():
    report=build_report()
    assert report['whole_units_semantically_verified'] and report['source_units']['einstein-1905:u0025']==226
