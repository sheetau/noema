from scripts import check_public_topics as checks


def test_every_reader_has_public_activity_descriptions_for_every_subject():
    assert checks.scope_checks()['every_reader_and_subject_covered']


def test_forbidden_or_unperformed_activities_cannot_be_filtered_out():
    assert checks.permission_checks()['forbidden_subject_not_removed_from_scope']


def test_topic_scope_remains_fixed_through_the_original_permission_period():
    assert checks.period_checks()['old_permission_and_time_content_preserved']


def test_fourteen_whole_unit_judgments_and_all_old_statements_are_preserved():
    assert checks.structure_checks()['preserved_whole_unit_reviews'] == 14
