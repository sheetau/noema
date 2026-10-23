from scripts.review_arbitrary_start_claim import build_report,record

def test_notice_and_consequence_cover_one_whole_sentence():
    r=build_report();s=record()
    assert r['source_units']=={'einstein-1905:u0058':175}
    assert r['verified_full_units']['einstein-1905']==1 and r['reviewed_math_elements']==1
    assert not r['all_spatial_trial_choices_exist_proved'] and not r['general_real_physical_derivation_proved']
    assert s['source_order_statements']==[282,283]
    assert ''.join(c['text'] for c in s['clauses'])==s['source']['text']
