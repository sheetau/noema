from scripts.review_physical_meaning_heading import build_report

def test_whole_fourth_heading():
    report=build_report()
    assert report['source_units']=={'einstein-1905:u0109':95}
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':1}
