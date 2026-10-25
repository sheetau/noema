from scripts.review_electron_mass_rewrite import records,build_report

def test_only_complete_equation_unit():
    rows=records();assert [r['unit'] for r in rows]==['einstein-1905:u0253']
    assert rows[0]['reviewed_prose_characters']==0 and rows[0]['unresolved']==[]

def test_review_provenance():assert build_report()['whole_units_semantically_verified']
