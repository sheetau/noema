from scripts import check_experimental_comparison as check


def test_interval_comparison_separates_invalid_inputs_from_disagreement():
    rows = check.numeric_checks()
    assert rows['touching_boundary'] == [True, True, False] * 2
    assert rows['only_light_speed_common'] == [True, False, True] * 2
    assert rows['negative_direct_lower'] == [True, True, False] * 2
    assert rows['zero_in_denominator_interval'] == [False] * 6


def test_ratio_bounds_enclose_all_values_and_overlap_has_a_witness():
    rows = check.polynomial_checks()
    assert rows['ratio_prediction_encloses_all_values_in_reported_bounds']['status'] == 'valid'
    assert rows['compatibility_has_a_maximum_lower_bound_witness']['status'] == 'valid'
    assert rows['overlap_requires_same_interval_centers']['status'] == 'invalid'


def test_joint_possibility_requires_matched_independent_records():
    result = check.binding_checks()
    rows = result['cases'][check.CORE]
    # Separately obtainable records do not supply a joint comparison.
    assert rows['no_joint'] == [False, False, False, False, True, False, False]
    # A possible comparison can disagree and need not actually have happened.
    assert rows['disjoint'] == [True, False, True, True, True, True, False]
    assert rows['actual_records'] == [True, True, False, True, True, True, True]
    assert rows['unmatched_direct_event'] == [False] * 7
    assert rows['circular_method'] == [False] * 7
    assert rows['direct_unit_rescaled'] == rows['baseline']
    assert result['unknown_independence_refused']


def test_authors_reason_does_not_assert_measured_agreement():
    row = check.attribution_check()
    assert row['quoted_targets'] == [
        ['claim', 'seul'], ['claim', 'seun'], ['reason', 'seun', 'seul']]
    assert not row['measurements_or_capability_executed']
    assert not row['agreement_or_disagreement_attributed']
