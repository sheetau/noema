from scripts.review_doppler_infinity import record,build_report

def test_literal_infinity_and_parenthesis_whole_sentence():
    r=record()
    assert r['unit']=='einstein-1905:u0192'
    assert not r['unresolved'] and r['source']['range']==[0,len(r['source']['text'])]
    assert len(r['clauses'])==3
    assert [m['id'] for m in r['source']['math']]==['M0336','M0337']

def test_pinned_record_validates():assert build_report()['whole_units_semantically_verified']
