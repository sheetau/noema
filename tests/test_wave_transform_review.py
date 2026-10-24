from scripts.review_wave_transform_application import records,build_report

def test_all_six_source_units_and_presentation():
    reviews=records()
    assert len(reviews)==6 and all(not r['unresolved'] for r in reviews)
    assert [r['unit'] for r in reviews]==['einstein-1905:u'+str(n).zfill(4) for n in range(182,188)]
    assert len(reviews[0]['clauses'])==2 and reviews[0]['source']['range'][0]==0

def test_pinned_whole_unit_records_validate():
    assert build_report()['whole_units_semantically_verified']
