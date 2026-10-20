from scripts import check_reversal_attribution as checks


def test_contextual_membership_cannot_shrink_to_successes():
    assert checks.scope_checks()['complete_contextual_scope_not_arbitrary_success_subset']


def test_case_supply_executes_existing_relations():
    assert checks.supply_checks()['native_incitation_incapacity_and_retention_executed']


def test_every_selected_case_and_the_same_public_are_required():
    assert checks.quantified_checks()['all_cases_of_all_selected_publics']


def test_author_attribution_does_not_execute_world_facts():
    assert checks.attribution_checks()['all_world_relations_unknown_without_execution']


def test_old_reviews_and_new_closed_statement_are_preserved():
    assert checks.structure_checks()['new_attributed_statements'] == 1
