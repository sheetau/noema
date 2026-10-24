from scripts.review_field_transformation_application import records,build_report


def test_complete_source_group():
    rs=records();assert [r['unit'] for r in rs]==[f'einstein-1905:u{n:04d}' for n in range(156,161)]
    assert all(r['unresolved']==[] and r['source_order_statements']==[153] for r in rs)
    assert [m['id'] for r in rs for m in r['source']['math']]==['M0290','M0291','M0292','M0293']
    assert all(r['source']['range']==[0,len(r['source']['text'])] for r in rs)


def test_pinned_evidence():assert build_report()['verified_full_units']['einstein-1905']==5
