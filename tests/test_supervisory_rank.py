from scripts.check_supervisory_rank import order_checks, source_checks, integration_checks, attribution_checks, structure


def test_greatest_position_allows_ties_and_differs_from_merely_maximal():
    r=order_checks()
    assert len(r['combinations'])==128
    assert not r['three_position_cases']['maximal_but_not_greatest']
    assert r['three_position_cases']['all_tied']


def test_current_supervisory_rank_and_the_assumed_position_are_both_bound():
    r=source_checks()['contrasts']
    assert r['subordinate'][:2]==[False,True]
    assert r['different_position'][:2]==[False,True]
    assert r['other_target_superior'][0]
    assert r['past_subordinate'][:2]==[False,True]
    assert r['no_past_position'][:2]==[False,True]


def test_rank_constraint_reaches_the_purposeful_causal_claim():
    assert integration_checks()['current_purpose_and_causation_executed']


def test_attribution_does_not_assert_actual_supervisory_authority():
    assert attribution_checks()['rank_assumption_purpose_and_cause_not_executed']


def test_existing_meanings_reviews_and_written_roundtrips_are_preserved():
    assert structure()['preserved_review_meanings']==11
