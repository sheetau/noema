from scripts.review_electron_comoving_equations import records,build_report

def test_four_complete_units():
    rows=records();assert [r['unit'] for r in rows]==[f'einstein-1905:u{n:04}' for n in range(246,250)]
    assert [r['reviewed_prose_characters'] for r in rows]==[190,0,131,0]
    assert all(r['unresolved']==[] for r in rows)

def test_review_provenance():assert build_report()['whole_units_semantically_verified']
