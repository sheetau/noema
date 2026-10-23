from scripts.review_simultaneity_conclusion import build_report

def test_whole_simultaneity_conclusion():
    report=build_report()
    assert report['whole_units_semantically_verified'] and sum(report['source_units'].values())==283
