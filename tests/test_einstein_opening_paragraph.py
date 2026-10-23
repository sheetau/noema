from scripts.check_einstein_opening_paragraph import build_report
def test_whole_paragraph_review_provenance():
    report=build_report()
    assert report['whole_unit_semantically_verified'] and report['source_nonblank_characters']==1023
