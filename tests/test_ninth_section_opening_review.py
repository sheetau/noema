from scripts.review_ninth_section_opening import records,build_report

def test_six_complete_unit_readings():
    rs=records();assert len(rs)==6 and all(r['unresolved']==[] for r in rs)
    assert [r['unit'] for r in rs]==[f'einstein-1905:u{n:04d}' for n in range(227,233)]
def test_review_provenance():assert build_report()['whole_units_semantically_verified']
