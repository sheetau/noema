from scripts.review_mirror_energy_principle import record,build_report

def test_two_complete_units():
    assert all(record(u)['decision']=='equivalent_under_stated_reading' for u in ('u0222','u0223'))

def test_review_evidence():assert build_report()['whole_units_semantically_verified']
