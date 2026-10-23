from scripts.review_differential_step import build_report,records

def test_four_units_share_the_inference_and_reexpression_in_pairs():
    r=build_report();a,b,c,d=records()
    assert r['source_units']=={'einstein-1905:u0054':40,'einstein-1905:u0055':0,'einstein-1905:u0056':4,'einstein-1905:u0057':0}
    assert r['verified_full_units']['einstein-1905']==4 and r['reviewed_math_elements']==3
    assert not r['general_real_chain_rule_proved']
    assert a['selection']==b['selection'] and c['selection']==d['selection']
    assert a['selection']!=c['selection']
