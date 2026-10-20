from scripts import check_enlightenment_requirement as checks


def test_freedom_is_required_and_other_content_is_not():
    assert checks.requirement_checks()['no_requirements_and_additional_requirements_rejected']


def test_requirement_and_minimum_use_the_same_public_scope():
    assert checks.composition_checks()['same_nonempty_scope_for_both_clauses']


def test_anaphora_specification_contrast_and_author_attribution():
    assert checks.discourse_checks()['same_goal_and_freedom_referents']


def test_whole_first_sentence_reading_and_unchanged_fourteen_reviews():
    assert checks.structure_checks()['sentence_nonblank_characters'] == 183
