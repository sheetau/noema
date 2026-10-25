from scripts.review_local_magnetic_radius import records,build_report

def test_third_item_both_displays_and_oder():
    rows=records();assert [r['unit'] for r in rows]==['einstein-1905:u0271','einstein-1905:u0272','einstein-1905:u0273','einstein-1905:u0274']
    assert [r['source_order_statements'] for r in rows]==[[437],[438],[439],[440]]
    assert [len(r['clauses']) for r in rows]==[6,1,1,1]
    assert [len(r['source']['math']) for r in rows]==[2,1,0,1]
    assert all(not r['unresolved'] for r in rows)

def test_review_provenance():assert build_report()['whole_units_semantically_verified']
