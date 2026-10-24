from scripts.review_kinematic_transition_claim import record,build_report


def test_whole_source_unit():
    r=record();assert r['unresolved']==[] and r['source_order_statements']==[150,151]
    assert r['source']['range']==[0,len(r['source']['text'])]


def test_pinned_evidence():assert build_report()['verified_full_units']['einstein-1905']==1
