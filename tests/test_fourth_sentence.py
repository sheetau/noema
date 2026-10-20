from scripts import check_fourth_sentence as checks


def test_referenced_kind_requires_valid_nonempty_references():
    assert checks.reference_checks()['candidate_can_differ_in_activity_and_time']


def test_bodily_reading_executes_history_kind_limitation_and_cause():
    assert checks.bodily_checks()['explanatory_adoption_does_not_replace_cause']


def test_correspondence_preserves_scope_without_executing_world_contents():
    assert checks.mapping_checks()['bodily_and_intellectual_contents_not_executed']


def test_only_fourth_sentence_assertions_change_and_old_judgments_survive():
    assert checks.structure_checks()['revised_statement_indices'] == [13, 53]


def test_sentence_partition_and_explicit_judgment_are_bound_to_sources():
    assert checks.reading_checks()['reviewed_fourth_sentence_characters'] == 136
