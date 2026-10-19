from scripts import check_insistent_framing as checks


def test_world_truth_does_not_supply_or_remove_emphatic_framing():
    assert len(checks.generic_checks()['combinations'])==24


def test_viewpoint_claim_and_focal_depiction_stay_bound():
    assert len(checks.scope_checks()['contrasts'])==16


def test_source_attributes_the_stance_without_a_literal_command():
    assert checks.source_checks()['seven_excerpt_statements_evaluated']


def test_actual_permission_and_emphasis_are_independent():
    assert len(checks.norm_checks()['combinations'])==8


def test_old_meanings_and_partial_review_scope_are_preserved():
    assert checks.structure()['preserved_review_selections']==11
