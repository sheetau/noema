from scripts.review_homogeneity_claim import build_report

def test_homogeneity_sentence_preserves_claim_and_proof_distinction():
    report=build_report()
    assert report['whole_units_semantically_verified']
    assert report['source_units']=={'einstein-1905:u0047':112}
    assert not report['homogeneity_implies_general_real_affinity_proved']
