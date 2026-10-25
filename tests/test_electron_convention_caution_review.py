from scripts.review_electron_convention_caution import record,build_report

def test_entire_sentence_and_shared_statement():
    r=record();assert r['unit']=='einstein-1905:u0259' and r['source_order_statements']==[426]
    assert r['unresolved']==[] and ''.join(c['text'] for c in r['clauses'])==r['source']['text']

def test_review_provenance():assert build_report()['whole_units_semantically_verified']
