from scripts.review_aberration_presentation import records,build_report

def test_whole_angle_introduction_and_display():
    rs=records()
    assert [r['unit'] for r in rs]==['einstein-1905:u0193','einstein-1905:u0194']
    assert all(not r['unresolved'] and r['source']['range']==[0,len(r['source']['text'])] for r in rs)
    assert len(rs[0]['clauses'])==2
    assert [m['id'] for r in rs for m in r['source']['math']]==['M0338','M0339','M0340']

def test_pinned_records_validate():assert build_report()['whole_units_semantically_verified']
