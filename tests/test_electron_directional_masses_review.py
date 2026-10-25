from scripts.review_electron_directional_masses import records,build_report

def test_complete_six_units_and_prior_rewrite_shared():
    rows=records();assert [r['unit'] for r in rows]==[f'einstein-1905:u{n:04}' for n in (252,254,255,256,257,258)]
    assert rows[0]['source_order_statements']==[423,422]
    assert all(r['unresolved']==[] for r in rows)

def test_review_provenance():assert build_report()['whole_units_semantically_verified']
