from scripts.review_second_principle import build_report

def test_whole_units():
    report=build_report()
    assert report['whole_units_semantically_verified'] and sum(report['source_units'].values())==253
