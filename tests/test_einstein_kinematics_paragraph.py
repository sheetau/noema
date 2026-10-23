from scripts.check_einstein_kinematics_paragraph import review_record,build_report

def test_two_sentences_share_the_same_circumstance():
    r=review_record();assert r['source_order_statements']==[217,218] and not r['unresolved']

def test_whole_paragraph_with_preserved_evidence():
    r=build_report();assert r['whole_unit_semantically_verified'] and r['source_nonblank_characters']==369
