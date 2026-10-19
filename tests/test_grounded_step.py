from scripts import check_grounded_step as checks


def test_single_contact_relocation():
    assert len(checks.generic_checks()['combinations'])==32


def test_body_foot_process_and_exterior_landing():
    assert len(checks.source_checks()['contrasts'])==23


def test_ordered_step_goal_bindings():
    assert len(checks.binding_checks()['contrasts'])==6


def test_permission_does_not_execute_bodily_goal():
    assert len(checks.norm_checks()['combinations'])==8


def test_preserved_meanings_and_roundtrips():
    assert checks.structure()['active_manuscript_unchanged']
