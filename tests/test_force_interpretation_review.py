from scripts.review_force_interpretation import records,build_report

def test_source_whole_paragraph():
    r=records()[0]
    assert r['unit']=='einstein-1905:u0173' and r['unresolved']==[]
    assert r['source_order_statements']==[358,163,164,165,166,359]
    assert r['source']['range']==[0,len(r['source']['text'])]
    assert ''.join(c['text'] for c in r['clauses'])==r['source']['text']
    assert r['reviewed_prose_characters']==700 and len(r['clauses'])==6
    assert [m['id'] for m in r['source']['math']]==['M0315','M0316','M0317']

def test_pinned_evidence():assert build_report()['verified_full_units']['einstein-1905']==1
