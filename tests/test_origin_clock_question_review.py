from scripts.review_origin_clock_question import build_report

def test_whole_origin_clock_setup_and_question():
    report=build_report()
    assert set(report['source_units'])=={'einstein-1905:u0118'}
    assert report['reviewed_math_elements']==4
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':1}
