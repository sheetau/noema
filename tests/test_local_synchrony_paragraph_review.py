from scripts.review_local_synchrony_paragraph import connection_checks,coverage_checks,review_record


def test_same_referents_and_formula():assert connection_checks()['displayed_equation_bound_to_same_hypothetical_three_readings']
def test_whole_source_coverage():assert coverage_checks()['six_sentences_and_display_connected_without_gaps']
def test_two_whole_unit_judgments():
    for i in (0,1):
        r=review_record(i);assert r['decision']=='equivalent_under_stated_reading' and r['unresolved']==[]
