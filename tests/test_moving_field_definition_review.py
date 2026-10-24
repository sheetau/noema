from scripts.review_moving_field_definition import records,build_report

def test_source_whole_units():
    rs=records();assert [r['unit'] for r in rs]==['einstein-1905:u0161','einstein-1905:u0162']
    assert all(r['unresolved']==[] and r['source_order_statements']==[154] for r in rs)
    assert [m['id'] for r in rs for m in r['source']['math']]==[f'M{n:04d}' for n in range(294,301)]
    assert all(r['source']['range']==[0,len(r['source']['text'])] for r in rs)

def test_pinned_evidence():assert build_report()['verified_full_units']['einstein-1905']==2
