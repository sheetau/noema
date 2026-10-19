from scripts import check_unpermitted_families as checks


def test_membership_permission_and_wellformedness():
    assert len(checks.generic_checks()['combinations'])==64


def test_norm_arguments_and_unknown_values():
    assert checks.scope_checks()['unknown_inputs_refused']==5


def test_individual_permission_survives_absent_broad_permission():
    assert checks.source_checks()['counterexample']['values']==[True,False,False]


def test_preserved_meanings_and_roundtrips():
    assert checks.structure()['active_manuscript_unchanged']
