from scripts.review_field_symmetry_conclusion import records,build_report

def test_source_whole_units():
    rs=records();assert [r['unit'] for r in rs]==[f'einstein-1905:u{n:04d}' for n in (167,168,169,170,171,172,282)]
    assert all(r['unresolved']==[] and r['source_order_statements']==[157,158,159] and r['attached_note_statements']==[160,161] for r in rs)
    assert [m['id'] for r in rs for m in r['source']['math']]==[f'M{n:04d}' for n in (312,313,314,443,444,445,446)]
    assert all(r['source']['range']==[0,len(r['source']['text'])] for r in rs)

def test_pinned_evidence():assert build_report()['verified_full_units']['einstein-1905']==7
