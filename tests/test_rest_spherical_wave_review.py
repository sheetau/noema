from scripts.review_rest_spherical_wave import records,build_report

def test_wave_setting_and_equation_whole_units():
    rs=records()
    assert [r['unit'] for r in rs]==['einstein-1905:u0087','einstein-1905:u0088']
    assert [r['reviewed_prose_characters'] for r in rs]==[203,1]
    assert all(r['unresolved']==[] for r in rs)
    assert build_report()['verified_full_units']=={'kant-1784':0,'einstein-1905':2}
