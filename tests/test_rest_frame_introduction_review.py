from scripts.review_rest_frame_introduction import review_record,build_report

def test_same_frame_from_hypothetical_introduction_to_naming():
    r=review_record();assert r['source_order_statements']==[221,222] and not r['unresolved']

def test_whole_unit_with_fixed_source_and_evidence():
    r=build_report();assert r['whole_unit_semantically_verified'] and r['source_nonblank_characters']==236
