from scripts.review_seventh_section_heading import record,build_report

def test_whole_source_unit():
    r=record();assert r['unresolved']==[] and r['source_order_statements']==[384]
    assert r['unit']=='einstein-1905:u0178'
    assert r['source']['text']=='§ 7. Theorie des Doppelerschen Prinzips und der Aberration.'
    assert r['source']['range']==[0,len(r['source']['text'])]

def test_pinned_evidence():assert build_report()['verified_full_units']['einstein-1905']==1
