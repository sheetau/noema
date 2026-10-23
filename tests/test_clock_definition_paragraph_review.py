from scripts.review_clock_definition_paragraph import review_record,build_report

def test_whole_paragraph_with_no_unresolved_items():
    record=review_record()
    assert record['source']['range']==[0,639] and not record['unresolved']
    assert len(record['requirements'])==8

def test_two_statements_and_shared_definition():
    assert review_record()['source_order_statements']==[229,230]

def test_validated_source_character_count():
    assert build_report()['source_units']=={'einstein-1905:u0011':545}
