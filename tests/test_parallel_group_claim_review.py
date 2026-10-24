from scripts.review_parallel_group_claim import records,build_report

def test_whole_source_units():
    rows=records();assert len(rows)==3 and all(r['unresolved']==[] for r in rows)
    assert rows[0]['source_order_statements']==[148,145,146]

def test_registered_evidence():assert build_report()['verified_full_units']['einstein-1905']==3
