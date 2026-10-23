from scripts.review_moving_trip_reading import build_report

def test_trial_equations_and_note_whole_units():
    report=build_report()
    assert report['whole_units_semantically_verified'] and sum(report['source_units'].values())==476
