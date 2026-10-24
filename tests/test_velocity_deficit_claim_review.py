from scripts.review_velocity_deficit_claim import build_report

def test_two_whole_units():
    r=build_report()
    assert r['source_units']=={'einstein-1905:u0143':195,'einstein-1905:u0144':0}
    assert r['reviewed_math_elements']==8
    assert r['verified_full_units']=={'kant-1784':0,'einstein-1905':2}
    assert not r['general_physical_derivation_proved']
