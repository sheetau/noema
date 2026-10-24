from scripts.review_observed_amplitude import records,build_report

def test_whole_task_names_and_square_ratio():
    rs=records()
    assert [r['unit'] for r in rs]==['einstein-1905:u0197','einstein-1905:u0198']
    assert all(not r['unresolved'] and r['source']['range']==[0,len(r['source']['text'])] for r in rs)
    assert len(rs[0]['clauses'])==3
    assert [m['id'] for r in rs for m in r['source']['math']]==['M0343','M0344','M0345']

def test_pinned_records_validate():assert build_report()['whole_units_semantically_verified']
