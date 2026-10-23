from scripts.review_final_transform_claim import build_report

def test_whole_units_and_explicit_branch_interpretation():
    report=build_report()
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':4}
    assert sum(report['source_units'].values())==117
    assert not report['semantic_equivalence_automatically_proved']
