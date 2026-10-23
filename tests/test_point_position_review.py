from scripts.review_point_position import review_record,build_report

def test_same_position_from_stationarity_to_possible_measurement():
    r=review_record();assert r['source_order_statements']==[223] and not r['unresolved']

def test_whole_unit_with_fixed_source_and_evidence():
    r=build_report();assert r['whole_unit_semantically_verified'] and r['source_nonblank_characters']==211
