from scripts import check_relative_difficulty as checks


def test_difficulty_keeps_actor_capacity_success_and_path_requirement_together():
    r = checks.generic_checks()
    assert len(r['combinations']) == 64 and len(r['contrasts']) == 27 and r['unknown_inputs_refused'] == 9


def test_self_work_and_future_independent_capacity_are_evaluated_natively():
    r = checks.source_checks()
    assert len(r['contrasts']) == 14 and r['unknown_inputs_refused'] == 4


def test_candidate_can_be_quoted_without_asserting_world_truth():
    assert checks.quotation_checks()['world_contents_unknown']


def test_existing_authored_text_and_twelve_reviews_are_unchanged():
    r = checks.structure_checks()
    assert r['new_definitions'] == 8 and r['new_primitives'] == 2
