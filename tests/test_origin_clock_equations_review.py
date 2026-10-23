from scripts.review_origin_clock_equations import build_report

def test_whole_origin_clock_equations():
    report=build_report()
    assert set(report['source_units'])=={f'einstein-1905:u{n:04d}' for n in range(119,123)}
    assert report['reviewed_math_elements']==5
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':4}
