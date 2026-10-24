from scripts.review_energy_frequency_law import record,build_report

def test_whole_source_covered():
    r=record();assert r['unit']=='einstein-1905:u0214' and r['reviewed_prose_characters']==133
    assert r['source']['math']==[]
    assert r['clauses'][0]['text']==r['source']['text']
    assert r['clauses'][0]['range']==r['source']['range']

def test_review_valid():assert build_report()['whole_units_semantically_verified']
