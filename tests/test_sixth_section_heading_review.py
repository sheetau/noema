from scripts.review_sixth_section_heading import record,build_report


def test_whole_source_unit():
    r=record();assert r['unresolved']==[] and r['source_order_statements']==[357]
    assert r['unit']=='einstein-1905:u0152'
    assert r['source']['text']=='§ 6. Transformation der Maxwell-Hertzschen Gleichungen für den leeren Raum. Über die Natur der bei Bewegung in einem Magnetfeld auftretenden elektromotorischen Kräfte.'
    assert r['source']['range']==[0,len(r['source']['text'])]


def test_pinned_evidence():assert build_report()['verified_full_units']['einstein-1905']==1
