from scripts.review_light_proof_task import record,build_report

def test_whole_proof_task_sentence():
    r=record()
    assert r['unit']=='einstein-1905:u0086' and r['reviewed_prose_characters']==293
    assert len(r['clauses'])==7 and r['unresolved']==[]
    assert build_report()['verified_full_units']=={'kant-1784':0,'einstein-1905':1}
