from scripts import check_internalized_state as checks


def test_actual_guided_experience_and_same_pattern_formation():
    r = checks.origin_checks()
    assert len(r['combinations']) == 16 and len(r['contrasts']) == 12
    assert r['unknown_inputs_refused'] == 9


def test_native_state_requires_actual_internal_causal_contribution():
    r = checks.contribution_checks()
    assert len(r['contrasts']) == 7 and r['unknown_inputs_refused'] == 2


def test_withdrawal_comparison_is_nonempty_and_endpoint_consistent():
    r = checks.degree_checks()
    assert len(r['candidate_subsets']) == 8 and r['unknown_inputs_refused'] == 2


def test_composed_reference_connects_to_actual_change_without_hiding_missing_values():
    r = checks.source_checks()
    assert len(r['contrasts']) == 9 and r['unknown_inputs_refused'] == 1


def test_content_can_be_quoted_without_asserting_world_truth():
    assert checks.quotation_checks()['world_contents_unknown']


def test_existing_authored_text_and_twelve_reviews_are_unchanged():
    r = checks.structure_checks()
    assert r['new_definitions'] == 6 and r['new_primitives'] == 5
