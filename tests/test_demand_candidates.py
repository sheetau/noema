from scripts import check_demand_candidates as checks


def test_concrete_contents_preserve_command_polarity_and_ruler_permission():
    assert checks.content_checks()['ruler_permission_not_negated']


def test_case_bindings_require_the_same_speaker_call_reference_and_code():
    assert checks.anchor_checks()['same_prior_speaker_call_reference_and_canonical_code']


def test_every_recipient_keeps_the_whole_requirement_and_own_choice():
    assert checks.row_checks()['every_fixed_recipient_has_one_whole_command_row']


def test_source_rows_bind_all_slots_of_the_checked_influence_profiles():
    assert checks.profile_checks()['all_record_slots_and_fixed_reference_passed']


def test_candidate_scope_contains_the_examples_without_excluding_other_kinds():
    assert checks.scope_checks()['all_four_required_but_more_candidates_allowed']


def test_existing_manuscript_and_reading_judgments_are_unchanged():
    assert checks.structure_checks()['new_semantically_reviewed_characters'] == 0
