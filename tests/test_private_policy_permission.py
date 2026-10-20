from scripts import check_private_policy_permission as check


def test_source_bindings():
    check.binding_checks()


def test_candidate_scope_and_adapter():
    check.scope_checks()


def test_permission_without_policy_execution():
    check.norm_checks()


def test_attribution_without_permission_execution():
    check.attribution_checks()


def test_preservation_and_roundtrips():
    check.structure_checks()
