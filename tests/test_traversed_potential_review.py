from scripts.review_traversed_potential import records,build_report

def test_whole_second_item_and_display():
    rows=records();assert [r['unit'] for r in rows]==['einstein-1905:u0269','einstein-1905:u0270']
    assert [r['source_order_statements'] for r in rows]==[[435],[436]]
    assert [len(r['clauses']) for r in rows]==[4,1]
    assert all(not r['unresolved'] and len(r['source']['math'])==1 for r in rows)

def test_review_provenance():assert build_report()['whole_units_semantically_verified']
