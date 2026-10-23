from scripts.review_sphere_zero_slice import build_report

def test_whole_K_zero_surface_expression():
    report=build_report()
    assert set(report['source_units'])=={'einstein-1905:u0112','einstein-1905:u0113'}
    assert report['reviewed_math_elements']==3
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':2}
