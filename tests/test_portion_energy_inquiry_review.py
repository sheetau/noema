from scripts.review_portion_energy_inquiry import record,build_report

def test_whole_source_covered():
    r=record();text=r['source']['text'];covered=set()
    for clause in r['clauses']:
        a,b=clause['range'];assert clause['text']==text[a:b];covered.update(range(a,b))
    assert all(i in covered for i,c in enumerate(text) if not c.isspace())
    assert r['reviewed_prose_characters']==221 and len(r['source']['math'])==2

def test_review_valid():assert build_report()['whole_units_semantically_verified']
