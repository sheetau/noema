from scripts import check_quantified_step_goals as checks


def test_existential_slots_use_a_shared_witness_pair():
    assert len(checks.generic_checks()['combinations'])==64


def test_physical_step_goals_preserve_named_roles():
    assert len(checks.physical_checks()['contrasts'])==8


def test_goal_quantifiers_stay_inside_the_attempted_content():
    assert len(checks.undertaking_checks()['combinations'])==16


def test_permission_scope_includes_unspecified_goals():
    assert checks.norm_checks()['countermodel']['values']==[False,True]


def test_preserved_meanings_and_roundtrips():
    assert checks.structure()['active_manuscript_unchanged']
