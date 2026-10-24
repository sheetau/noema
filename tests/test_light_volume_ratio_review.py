from scripts.review_light_volume_ratio import records,build_report

def test_whole_sources_covered():
    rs=records();assert [r['unit'] for r in rs]==['einstein-1905:u0208','einstein-1905:u0209']
    assert [len(r['source']['math']) for r in rs]==[2,1]
    for r in rs:
        assert r['clauses'][0]['text']==r['source']['text']
        assert r['clauses'][0]['range']==r['source']['range']

def test_reviews_valid():assert build_report()['whole_units_semantically_verified']
