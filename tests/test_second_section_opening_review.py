from scripts.review_second_section_opening import build_report

def test_whole_units():
    report=build_report()
    assert report['whole_units_semantically_verified'] and [u['nonblank_characters'] for u in report['units']]==[40,161]
