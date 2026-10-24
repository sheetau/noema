from scripts.review_aberration_specialization import records,build_report

def test_whole_named_general_law_and_special_display():
    rs=records()
    assert [r['unit'] for r in rs]==['einstein-1905:u0195','einstein-1905:u0196']
    assert all(not r['unresolved'] and r['source']['range']==[0,len(r['source']['text'])] for r in rs)
    assert len(rs[0]['clauses'])==2
    assert [m['id'] for r in rs for m in r['source']['math']]==['M0341','M0342']

def test_pinned_records_validate():assert build_report()['whole_units_semantically_verified']
