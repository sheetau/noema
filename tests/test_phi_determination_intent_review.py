from scripts.review_phi_determination_intent import record,build_report

def test_unknown_phi_and_intention_whole_sentence():
    r=record()
    assert r['unit']=='einstein-1905:u0092' and r['reviewed_prose_characters']==109
    assert r['unresolved']==[] and r['source_order_statements']==[309]
    assert build_report()['verified_full_units']=={'kant-1784':0,'einstein-1905':1}
