from scripts.review_closing_acknowledgment import records,build_report

def test_closing_acknowledgment_and_two_dates():
    rows=records();assert [r['unit'] for r in rows]==['einstein-1905:u0276','einstein-1905:u0277','einstein-1905:u0278']
    assert [r['source_order_statements'] for r in rows]==[[441],[442],[443]]
    assert [len(r['clauses']) for r in rows]==[5,2,2]
    assert all(not r['unresolved'] and not r['source']['math'] for r in rows)

def test_review_provenance():assert build_report()['whole_units_semantically_verified']
