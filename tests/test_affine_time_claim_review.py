from scripts.review_affine_time_claim import build_report,records

def test_formula_and_qualifications_cover_three_whole_units():
    r=build_report();intro,formula,qualifications=records()
    assert r['source_units']=={'einstein-1905:u0062':51,'einstein-1905:u0063':1,'einstein-1905:u0064':98}
    assert r['reviewed_math_elements']==7 and r['verified_full_units']['einstein-1905']==3
    assert not r['general_real_physical_derivation_proved']
    assert intro['source_order_statements']==formula['source_order_statements']==[286]
    assert qualifications['source_order_statements']==[286,287,288]
    assert all(''.join(c['text'] for c in s['clauses'])==s['source']['text'] for s in (intro,formula,qualifications))
