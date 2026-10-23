from scripts.review_transverse_derivative_claim import build_report,records

def test_sentence_and_two_equations_share_the_same_inference():
    r=build_report();sentence,y,z=records()
    assert r['source_units']=={'einstein-1905:u0059':172,'einstein-1905:u0060':0,'einstein-1905:u0061':0}
    assert r['reviewed_math_elements']==5 and r['verified_full_units']['einstein-1905']==3
    assert not r['general_real_physical_derivation_proved'] and not r['concrete_tau_transformation_derived']
    assert sentence['source_order_statements']==[284,285]
    assert y['source_order_statements']==z['source_order_statements']==[285] and y['selection']==z['selection']
    assert all(''.join(c['text'] for c in s['clauses'])==s['source']['text'] for s in (sentence,y,z))
