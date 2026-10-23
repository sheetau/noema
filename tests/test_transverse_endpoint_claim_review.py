from scripts.review_transverse_endpoint_claim import build_report

def test_whole_meaning_question_selection_and_both_endpoint_displays():
    report=build_report()
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':4}
    assert report['source_units']=={'einstein-1905:u0097':235,'einstein-1905:u0098':0,'einstein-1905:u0099':3,'einstein-1905:u0100':0}
    assert report['reviewed_math_elements']==11
