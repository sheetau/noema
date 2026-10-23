from scripts.review_frame_instruments import build_report

def test_whole_initial_frame_setting():
    report=build_report()
    assert report['whole_units_semantically_verified'] and sum(report['source_units'].values())==361
