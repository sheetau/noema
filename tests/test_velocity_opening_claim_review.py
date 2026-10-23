from scripts.review_velocity_opening_claim import build_report


def test_whole_velocity_opening_claim():
    report=build_report()
    assert report['source_units']=={f'einstein-1905:u{n:04d}':c for n,c in zip(range(129,133),(40,102,0,27))}
    assert report['reviewed_math_elements']==7
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':4}
