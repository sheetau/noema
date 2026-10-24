from scripts.review_pressure_leading_approximation import record,build_report

def test_two_complete_units():
    assert all(record(u)['decision']=='equivalent_under_stated_reading' for u in ('u0224','u0225'))

def test_review_evidence():assert build_report()['whole_units_semantically_verified']
