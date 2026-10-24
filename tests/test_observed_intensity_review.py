from scripts.review_observed_intensity import record,build_report

def test_entire_intensity_sentence_is_reviewed():
    r=record();assert r['unit']=='einstein-1905:u0201' and r['reviewed_prose_characters']==160
    assert all(x['decision']=='satisfied' for x in r['requirements']) and not r['unresolved']

def test_whole_review_bindings_and_evidence():assert build_report()['verified_full_units']['einstein-1905']==1
