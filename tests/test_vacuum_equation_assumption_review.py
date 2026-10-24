from scripts.review_vacuum_equation_assumption import records,build_report


def test_complete_source_group():
    rs=records();assert [r['unit'] for r in rs]==[f'einstein-1905:u{n:04d}' for n in range(153,156)]
    assert all(r['unresolved']==[] and r['source_order_statements']==[152] for r in rs)
    assert [m['id'] for r in rs for m in r['source']['math']]==['M0286','M0287','M0288','M0289']
    assert all(r['source']['range']==[0,len(r['source']['text'])] for r in rs)


def test_pinned_evidence():assert build_report()['verified_full_units']['einstein-1905']==3
