from scripts.review_deflection_speed_determination import records,build_report

def test_complete_argument_and_formula():
    rows=records();assert [r['unit'] for r in rows]==['einstein-1905:u0266','einstein-1905:u0267']
    assert rows[0]['reviewed_prose_characters']>300 and rows[1]['reviewed_prose_characters']==0
    assert all(not r['unresolved'] for r in rows)
    assert [r['source_order_statements'] for r in rows]==[[432],[433]]

def test_review_provenance():assert build_report()['whole_units_semantically_verified']
