from scripts.review_moving_ellipsoid import build_report


def test_whole_general_moving_ellipsoid_and_axes():
    report=build_report()
    assert set(report['source_units'])=={'einstein-1905:u0114','einstein-1905:u0115'}
    assert report['reviewed_math_elements']==1
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':2}
