from scripts.review_same_light_portion import records,build_report


def test_whole_source_coverage():
    reviews=records();assert [r['unit'] for r in reviews]==['einstein-1905:u0203','einstein-1905:u0204']
    assert [r['reviewed_prose_characters'] for r in reviews]==[475,0]
    assert [len(r['source']['math']) for r in reviews]==[6,1]
    for r in reviews:
        covered=set()
        for clause in r['clauses']:
            a,b=clause['range'];assert clause['text']==r['source']['text'][a:b];covered.update(range(a,b))
        assert all(i in covered for i,c in enumerate(r['source']['text']) if not c.isspace())
        assert not r['unresolved']


def test_pinned_whole_unit_records_validate():
    assert build_report()['whole_units_semantically_verified']
