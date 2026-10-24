from scripts.review_electromotive_wording import records,build_report

def test_whole_first_wording():
    r=records()[0]
    assert r['unit']=='einstein-1905:u0174' and r['unresolved']==[]
    assert r['source']['range']==[0,len(r['source']['text'])]
    assert ''.join(c['text'] for c in r['clauses'])==r['source']['text']
    assert r['reviewed_prose_characters']==386 and len(r['clauses'])==5
    assert [m['id'] for m in r['source']['math']]==['M0318']

def test_pinned_evidence():assert build_report()['verified_full_units']['einstein-1905']==1
