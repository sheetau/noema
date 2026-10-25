from scripts.review_complete_motion_expression import record,build_report

def test_complete_source_and_selection():
    r=record();assert r['unit']=='einstein-1905:u0275'
    assert r['source_order_statements']==[445] and len(r['clauses'])==4
    assert not r['unresolved'] and not r['source']['math']

def test_review_provenance():assert build_report()['whole_units_semantically_verified']
