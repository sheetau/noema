from scripts import check_affection_sentence as checks


def test_same_people_and_scene():
    assert checks.scope_checks()['same_people_and_scene_for_both_conjuncts']


def test_focus_background_independent_of_truth():
    assert checks.focus_checks()['background_independent_of_world_truth']


def test_attribution_and_order():
    assert checks.discourse_checks()['foreground_and_focus_scope_preserved']


def test_existing_native_evidence_and_first_sentence():
    assert checks.reused_checks()['first_sentence_review_preserved']


def test_roundtrips_and_review_bindings():
    assert checks.structure_checks()['roundtrips']
