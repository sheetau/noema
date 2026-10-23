from scripts.review_transformation_heading import build_report

def test_whole_transformation_heading():
    report=build_report()
    assert report['whole_units_semantically_verified'] and sum(report['source_units'].values())==136
