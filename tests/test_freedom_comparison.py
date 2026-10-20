from scripts import check_freedom_comparison as checks


def test_minimum_allows_ties_but_rejects_other_lower_forms_and_invalid_orders():
    assert checks.minimum_checks()['native_rce_rcd']


def test_comparison_uses_exact_public_use_content_without_executing_it():
    assert checks.binding_checks()['permission_execution_and_attainment_unknown_without_execution']


def test_same_nonempty_public_scope_and_unknown_inputs():
    assert checks.scope_checks()['unknown_inputs_refused'] == 4


def test_all_existing_statements_and_fourteen_reviews_preserved():
    assert checks.structure_checks()['preserved_whole_unit_reviews'] == 14
