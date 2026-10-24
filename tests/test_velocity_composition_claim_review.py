from scripts.review_velocity_composition_claim import build_report


def test_two_whole_units_and_explicit_correction():
    r=build_report()
    assert r['source_units']=={'einstein-1905:u0139':92,'einstein-1905:u0140':0}
    assert r['reviewed_math_elements']==4
    assert r['source_corrections'][0]['correction_id']=='einstein-1905:M0257:denominator-cos'
    assert r['verified_full_units']=={'kant-1784':0,'einstein-1905':2}
    assert not r['general_physical_derivation_proved']
