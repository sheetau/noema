from scripts.review_mirror_wave_quantities import UNITS,record,build_report

def test_whole_sources():
    records=[record(unit) for unit in UNITS]
    for r in records:
        text=r['source']['text'];covered=set()
        for clause in r['clauses']:
            a,b=clause['range'];assert clause['text']==text[a:b];covered.update(range(a,b))
        assert all(i in covered for i,c in enumerate(text) if not c.isspace())
    assert sum(r['reviewed_prose_characters'] for r in records)==184
    assert sum(len(r['source']['math']) for r in records)==6

def test_reviews_valid():assert build_report()['whole_units_semantically_verified']
