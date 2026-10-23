from scripts.review_observer_contrast import build_report

def test_whole_length_gloss_and_observer_contrast():
    report=build_report()
    assert report['whole_units_semantically_verified'] and sum(report['source_units'].values())==236
