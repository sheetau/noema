from scripts.review_sphere_setting import build_report

def test_whole_sphere_setting_equation_and_note():
    report=build_report()
    assert set(report['source_units'])=={'einstein-1905:u0110','einstein-1905:u0111','einstein-1905:u0281'}
    assert report['reviewed_math_elements']==6
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':3}
