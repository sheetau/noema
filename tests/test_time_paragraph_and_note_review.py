from scripts.review_time_paragraph_and_note import review_record,build_report

def test_four_sentence_time_paragraph_complete_under_reading():
    r=review_record('einstein-1905:u0010');assert r['source_order_statements']==[224,225,226,227] and not r['unresolved']

def test_author_note_with_same_anchor_and_local_caveat():
    r=review_record('einstein-1905:u0279');assert r['source_order_statements']==[228] and not r['unresolved']

def test_two_units_counted_separately_without_sentence_overlap():
    r=build_report();assert r['source_units']=={'einstein-1905:u0010':560,'einstein-1905:u0279':185}
