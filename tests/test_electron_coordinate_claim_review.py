from scripts.review_electron_coordinate_claim import records,build_report

def test_complete_unit_reading():
    r=records()[0];assert r['unit']=='einstein-1905:u0245' and r['unresolved']==[]
    assert len(r['clauses'])==9 and len(r['source']['math'])==7
    assert r['reviewed_prose_characters']==366

def test_review_provenance():assert build_report()['whole_units_semantically_verified']
