from scripts.review_experimental_list_opening import record,build_report

def test_complete_source_and_selection():
    r=record();assert r['unit']=='einstein-1905:u0265'
    assert r['source_order_statements']==[444] and len(r['clauses'])==4
    assert not r['unresolved'] and not r['source']['math']

def test_review_provenance():assert build_report()['whole_units_semantically_verified']
