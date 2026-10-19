from scripts.check_relative_past import generic_checks, source_checks, attribution_checks, structure


def test_distance_is_relative_to_reference_not_every_later_state():
    assert generic_checks()['contrasts']['recent_but_future_far']==[False,True]


def test_actual_release_and_depiction_keep_the_same_temporal_anchor():
    assert source_checks()['actual_transition_witness_and_depiction_executed']


def test_figurative_attribution_does_not_assert_natures_actual_speech():
    assert attribution_checks()['all_temporal_and_causal_facts_unknown']


def test_existing_whole_unit_reviews_and_text_are_preserved():
    assert structure()['preserved_review_meanings']==11
