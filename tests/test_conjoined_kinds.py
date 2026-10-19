from scripts import check_conjoined_kinds as checks


def test_generalizations_cannot_pool_away_a_kind():
    assert checks.generic_checks()['pooling_counterexample_verified']


def test_source_case_identity_and_classification():
    assert checks.binding_checks()['each_case_identity_preserved']


def test_native_response_and_classification_limit():
    assert checks.native_checks()['native_capacity_and_conditional_profile_executed']


def test_meaning_conventions_and_existing_manuscript():
    assert checks.structure_checks()['active_registry_unchanged']
