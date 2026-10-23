from scripts.review_comoving_time_task import build_report

def test_three_sentences_and_candidate_task_not_solved_transformation():
    report=build_report()
    assert report['whole_units_semantically_verified']
    assert report['source_units']=={'einstein-1905:u0048':314}
    assert not report['concrete_tau_transformation_derived']
    assert not report['general_physical_invariance_proved']
