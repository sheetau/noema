from scripts.review_convective_transformation_claim import records,build_report

def test_four_complete_unit_readings():
    rs=records();assert len(rs)==4 and all(r['unresolved']==[] for r in rs)
    assert [r['unit'] for r in rs]==[f'einstein-1905:u{n:04d}' for n in range(233,237)]
    assert sum(r['reviewed_prose_characters'] for r in rs)==150

def test_review_provenance():assert build_report()['whole_units_semantically_verified']
