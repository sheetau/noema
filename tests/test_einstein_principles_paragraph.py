from scripts.check_einstein_principles_paragraph import review_record,build_report

def test_all_four_sentences_and_the_same_postulates():
    r=review_record();assert r['source_order_statements']==[213,214,215,216] and not r['unresolved']
def test_whole_unit_judgment_with_math_and_prior_evidence():
    r=build_report();assert r['whole_unit_semantically_verified'] and r['source_nonblank_characters']==1244
