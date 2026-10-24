from scripts.review_distant_wave_source import records,build_report

def test_whole_unit():
    r=records()[0]
    assert r['unit']=='einstein-1905:u0179' and r['unresolved']==[]
    assert r['source']['range']==[0,len(r['source']['text'])]
    assert ''.join(c['text'] for c in r['clauses'])==r['source']['text']
    assert r['reviewed_prose_characters']==198 and len(r['clauses'])==4
    assert [s['index'] for s in r['selection']['statements']]==[363]
    assert [m['id'] for m in r['source']['math']]==['M0319']

def test_pinned_evidence():assert build_report()['verified_full_units']['einstein-1905']==1
