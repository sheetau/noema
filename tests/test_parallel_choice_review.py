from scripts.review_parallel_choice import build_report

def test_whole_frame_motion_and_symmetry_permission():
    report=build_report()
    assert report['whole_units_semantically_verified'] and sum(report['source_units'].values())==526
