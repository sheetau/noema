from scripts.review_light_energy_ratio import records,build_report

def test_whole_sources_covered():
    rs=records();assert [r['unit'] for r in rs]==[f'einstein-1905:u{n:04d}' for n in range(210,214)]
    assert [r['reviewed_prose_characters'] for r in rs]==[140,0,39,0]
    assert [len(r['source']['math']) for r in rs]==[2,1,1,1]
    for r in rs:
        assert r['clauses'][0]['text']==r['source']['text']
        assert r['clauses'][0]['range']==r['source']['range']

def test_reviews_valid():assert build_report()['whole_units_semantically_verified']
