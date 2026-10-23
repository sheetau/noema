from scripts.review_wave_compatibility_conclusion import record,build_report

def test_two_sentences_whole_unit():
    r=record()
    assert r['unit']=='einstein-1905:u0091' and r['reviewed_prose_characters']==177
    assert r['unresolved']==[] and r['source_order_statements']==[307,308]
    assert build_report()['verified_full_units']=={'kant-1784':0,'einstein-1905':1}
