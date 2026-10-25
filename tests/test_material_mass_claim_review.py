from scripts.review_material_mass_claim import record,build_report

def test_whole_material_extension_sentence():
    r=record();assert r['unit']=='einstein-1905:u0260' and r['source_order_statements']==[427]
    assert r['unresolved']==[] and ''.join(c['text'] for c in r['clauses'])==r['source']['text']

def test_review_provenance():assert build_report()['whole_units_semantically_verified']
