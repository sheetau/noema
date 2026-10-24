from scripts.review_light_ellipsoid_surface import records,build_report

def test_whole_sources_covered():
    rs=records();assert [r['reviewed_prose_characters'] for r in rs]==[98,0]
    for r in rs:
        assert r['clauses'][0]['text']==r['source']['text']
        assert r['clauses'][0]['range']==r['source']['range']
        assert len(r['source']['math'])==1

def test_reviews_valid():assert build_report()['whole_units_semantically_verified']
