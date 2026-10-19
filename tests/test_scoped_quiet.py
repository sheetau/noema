from scripts import check_scoped_quiet as checks


def test_absence_binds_subject_episode_occurrence_quality_and_time():
    assert len(checks.binding_checks()['combinations'])==64


def test_absence_requires_valid_scope_and_known_inputs():
    assert len(checks.scope_checks()['contrasts'])==12


def test_outward_quiet_is_independent_of_inactivity_and_inner_state():
    assert len(checks.independent_checks()['combinations'])==16


def test_old_meanings_readings_sources_and_notation_preserved():
    assert checks.structure()['preserved_review_selections']==11
