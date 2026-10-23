from scripts.review_reciprocal_shape_results import build_report

def test_whole_reciprocal_shape_result():
    report=build_report()
    assert set(report['source_units'])=={'einstein-1905:u0117'}
    assert report['reviewed_math_elements']==0
    assert report['verified_full_units']=={'kant-1784':0,'einstein-1905':1}
