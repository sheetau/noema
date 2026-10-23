from scripts.review_rest_system_time import review_record


def test_whole_rest_system_time_naming():
    r=review_record();assert r['decision']=='equivalent_under_stated_reading' and not r['unresolved']
