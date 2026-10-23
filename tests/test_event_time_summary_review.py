from scripts.review_event_time_summary import review_record


def test_whole_definition_summary():
    r=review_record();assert r['decision']=='equivalent_under_stated_reading' and not r['unresolved']
