from scripts.review_electron_transformed_dynamics import records,build_report

def test_two_complete_units():
    rows=records();assert [r['unit'] for r in rows]==['einstein-1905:u0250','einstein-1905:u0251']
    assert [r['reviewed_prose_characters'] for r in rows]==[104,0]
    assert all(r['unresolved']==[] for r in rows)

def test_review_provenance():assert build_report()['whole_units_semantically_verified']
