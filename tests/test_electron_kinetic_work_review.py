from scripts.review_electron_kinetic_work import records,build_report

def test_both_complete_units_and_printed_formula():
    rows=records();assert [r['unit'] for r in rows]==['einstein-1905:u0261','einstein-1905:u0262']
    assert rows[0]['reviewed_prose_characters']>500 and rows[1]['reviewed_prose_characters']==0
    assert all(not r['unresolved'] for r in rows)
    assert [r['source_order_statements'] for r in rows]==[[428],[429]]

def test_review_provenance():assert build_report()['whole_units_semantically_verified']
