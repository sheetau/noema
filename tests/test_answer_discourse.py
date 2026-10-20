from scripts import check_answer_discourse as check


def test_private_policy_projection_preserves_conditions():
    check.split_checks()


def test_whole_content_and_scope():
    check.content_checks()


def test_self_answer_contrast_and_causal_qualification():
    check.discourse_checks()


def test_reading_preservation_and_roundtrips():
    check.structure_checks()
