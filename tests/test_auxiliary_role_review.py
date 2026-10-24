from scripts.review_auxiliary_role import records,build_report

def test_whole_auxiliary_role():
    r=records()[0]
    assert r['unit']=='einstein-1905:u0176' and r['unresolved']==[]
    assert r['source']['range']==[0,len(r['source']['text'])]
    assert ''.join(c['text'] for c in r['clauses'])==r['source']['text']
    assert r['reviewed_prose_characters']==302 and len(r['clauses'])==4
    assert [s['index'] for s in r['selection']['statements']]==[169,170,171,172]
    assert r['source']['math']==[]

def test_pinned_evidence():assert build_report()['verified_full_units']['einstein-1905']==1
