from scripts.review_convective_relativity_claim import records,build_report

def test_complete_unit_reading():
    rs=records();assert len(rs)==1 and rs[0]['unresolved']==[]
    assert rs[0]['unit']=='einstein-1905:u0237'
    assert len(rs[0]['clauses'])==8

def test_review_provenance():assert build_report()['whole_units_semantically_verified']
