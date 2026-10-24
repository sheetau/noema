from scripts.review_optical_problem_method import record,build_report

def test_whole_three_sentence_reading():
    r=record();assert len(r['clauses'])==3 and r['unresolved']==[]
    assert all(c['statements']==[406] for c in r['clauses'])

def test_registered_evidence():assert build_report()['whole_units_semantically_verified']
