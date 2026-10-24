from scripts.review_wave_display import records,build_report

def test_whole_units():
    rows=records()
    assert [r['unit'] for r in rows]==['einstein-1905:u0180','einstein-1905:u0181']
    assert [r['reviewed_prose_characters'] for r in rows]==[0,109]
    assert [[s['index'] for s in r['selection']['statements']] for r in rows]==[[364],[365]]
    for r in rows:
        assert r['unresolved']==[] and r['source']['range']==[0,len(r['source']['text'])]
        assert ''.join(c['text'] for c in r['clauses'])==r['source']['text']
    assert [[m['id'] for m in r['source']['math']] for r in rows]==[['M0320'],['M0321','M0322','M0323']]

def test_pinned_evidence():assert build_report()['verified_full_units']['einstein-1905']==2
