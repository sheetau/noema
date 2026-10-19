from scripts import check_unselected_continuation as checks


def test_practical_selection_keeps_actor_judgment_target_and_polarity():
    r = checks.selection_checks()
    assert len(r['combinations']) == 16 and len(r['contrasts']) == 5 and r['unknown_inputs_refused'] == 3


def test_unselected_and_contrary_decision_occurrences_are_distinct():
    r = checks.occurrence_checks()
    assert len(r['combinations']) == 8 and r['unknown_inputs_refused'] == 2


def test_no_fresh_selection_profile_is_nonempty_and_endpoint_consistent():
    r = checks.degree_checks()
    assert len(r['selection_subsets']) == 8 and len(r['contrasts']) == 5 and r['unknown_inputs_refused'] == 3


def test_disposition_differs_from_only_deliberated_success_and_current_occurrence():
    r = checks.source_checks()
    assert len(r['contrasts']) == 11 and r['unknown_inputs_refused'] == 1


def test_quotation_preserves_unknown_world_truth():
    assert checks.quotation_checks()['world_contents_unknown']


def test_existing_authored_text_and_twelve_reviews_are_unchanged():
    r = checks.structure_checks()
    assert r['new_definitions'] == 5 and r['new_primitives'] == 2
