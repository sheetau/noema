from scripts.review_consistent_synchrony import review_record


def test_whole_assumption_review():
    r=review_record();assert r['decision']=='equivalent_under_stated_reading' and not r['unresolved']
