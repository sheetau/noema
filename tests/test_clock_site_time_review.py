from scripts.review_clock_site_time import build_report

def test_complete_unit_keeps_first_sentence_and_avoids_double_count():
    report=build_report()
    assert report['whole_units_semantically_verified']
    assert report['source_units']=={'einstein-1905:u0045':602}
    assert report['incorporated_sentence_characters_not_added_again']==176
