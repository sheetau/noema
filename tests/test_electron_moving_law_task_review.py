from scripts.review_electron_moving_law_task import records,build_report
def test_complete_unit_reading():
    r=records()[0];assert r['unit']=='einstein-1905:u0244' and r['unresolved']==[]
    assert len(r['clauses'])==7 and r['reviewed_prose_characters']==167
def test_review_provenance():assert build_report()['whole_units_semantically_verified']
