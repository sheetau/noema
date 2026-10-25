from scripts.review_kinetic_energy_consequences import records,build_report

def test_both_complete_units_and_scopes():
    rows=records();assert [r['unit'] for r in rows]==['einstein-1905:u0263','einstein-1905:u0264']
    assert all(r['reviewed_prose_characters']>90 and not r['unresolved'] for r in rows)
    assert [r['source_order_statements'] for r in rows]==[[430],[431]]

def test_review_provenance():assert build_report()['whole_units_semantically_verified']
