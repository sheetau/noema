from scripts.review_shape_dimension_paragraph import build_report

def test_whole_three_sentence_shape_paragraph():
    report=build_report()
    assert set(report['source_units'])=={'einstein-1905:u0116'}
    assert report['reviewed_math_elements']==6
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':1}
