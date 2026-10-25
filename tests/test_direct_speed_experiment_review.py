from scripts.review_direct_speed_experiment import record,build_report

def test_whole_sentence_including_example():
    r=record();assert r['unit']=='einstein-1905:u0268' and r['source_order_statements']==[434]
    assert r['reviewed_prose_characters']>150 and not r['unresolved'] and len(r['clauses'])==4

def test_review_provenance():assert build_report()['whole_units_semantically_verified']
