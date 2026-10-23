from scripts.review_light_time_expansion import build_report,records


def test_sentence_and_both_equation_halves_share_one_conditional_reexpression():
    report=build_report()
    assert report['source_units']=={'einstein-1905:u0051':116,'einstein-1905:u0052':0,'einstein-1905:u0053':0}
    assert report['verified_full_units']['einstein-1905']==3
    assert report['reviewed_math_elements']==3
    assert not report['general_physical_derivation_proved']
    first,left,right=records()
    assert first['selection']==left['selection']==right['selection']
