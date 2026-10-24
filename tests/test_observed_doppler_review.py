from scripts.review_observed_doppler import records,build_report

def test_two_whole_units_and_all_math_references():
    reviews=records()
    assert [r['unit'] for r in reviews]==['einstein-1905:u0188','einstein-1905:u0189']
    assert all(not r['unresolved'] and r['source']['range']==[0,len(r['source']['text'])] for r in reviews)
    assert [m['id'] for r in reviews for m in r['source']['math']]==['M0328','M0329','M0330','M0331','M0332','M0333']

def test_pinned_records_validate():assert build_report()['whole_units_semantically_verified']
