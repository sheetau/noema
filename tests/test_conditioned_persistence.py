from scripts import check_conditioned_persistence as checks


def test_conditional_continuations():
    assert checks.generic_checks()['branch_local_points_preserved']


def test_same_activity_causes_the_local_result():
    assert checks.binding_checks()['same_act_cause_required']


def test_native_capacity_and_futures():
    assert checks.native_checks()['native_current_capacity_executed']


def test_preserved_meanings_and_reviews():
    assert checks.reused_checks()['preserved_reviewed_sentence_characters'] == 247


def test_unasserted_profile_and_roundtrips():
    assert checks.structure_checks()['new_profile_not_asserted']
