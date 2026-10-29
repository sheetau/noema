from scripts import check_kant_emancipation_integration_visible as check


def test_current_nature_adapter():
    check.nature_adapter_checks()


def test_current_individual_scope():
    check.individual_scope_checks()
