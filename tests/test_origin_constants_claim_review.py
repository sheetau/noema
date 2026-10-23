from scripts.review_origin_constants_claim import record,build_report

def test_whole_unit_reading_preserves_two_sentences():
    r=record()
    assert r['unit']=='einstein-1905:u0085' and r['reviewed_prose_characters']==204
    assert len(r['clauses'])==4 and r['unresolved']==[]
    assert build_report()['verified_full_units']=={'kant-1784':0,'einstein-1905':1}
