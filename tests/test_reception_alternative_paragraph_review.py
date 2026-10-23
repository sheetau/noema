from scripts.review_reception_alternative_paragraph import review_record,build_report,discourse_checks

def test_whole_source_and_shared_references():
    record=review_record()
    assert record['source']['range']==[0,569] and not record['unresolved']
    assert len(record['requirements'])==8 and record['source_order_statements']==[231,232,233]

def test_native_three_sentence_presentation():
    assert discourse_checks()['modal_contrast_and_forward_reference_preserved']

def test_whole_unit_review_validation():
    assert build_report()['source_units']=={'einstein-1905:u0012':491}
