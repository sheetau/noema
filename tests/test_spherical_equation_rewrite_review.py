from scripts.review_spherical_equation_rewrite import records,build_report

def test_sphere_rewrite_and_equation_whole_units():
    rs=records()
    assert [r['unit'] for r in rs]==['einstein-1905:u0089','einstein-1905:u0090']
    assert [r['reviewed_prose_characters'] for r in rs]==[105,1]
    assert all(r['unresolved']==[] for r in rs)
    assert build_report()['verified_full_units']=={'kant-1784':0,'einstein-1905':2}
