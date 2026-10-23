from scripts.review_event_coordinate_task import build_report

def test_complete_correspondence_and_equation_task_sentence():
    report=build_report()
    assert report['whole_units_semantically_verified']
    assert report['source_units']=={'einstein-1905:u0046':227}
