from scripts.review_doppler_specialization import records,build_report

def test_whole_two_sentences_and_display():
    reviews=records()
    assert [r['unit'] for r in reviews]==['einstein-1905:u0190','einstein-1905:u0191']
    assert all(not r['unresolved'] and r['source']['range']==[0,len(r['source']['text'])] for r in reviews)
    assert len(reviews[0]['clauses'])==2
    assert [m['id'] for r in reviews for m in r['source']['math']]==['M0334','M0335']

def test_pinned_records_validate():assert build_report()['whole_units_semantically_verified']
