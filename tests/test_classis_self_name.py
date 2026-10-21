from scripts.check_classis_self_name import naming_checks,classification_checks,structure_checks


def test_same_user_target_name_community_and_honorific():naming_checks()


def test_self_name_does_not_establish_classification():classification_checks()


def test_source_spans_archival_title_and_roundtrips():structure_checks()
