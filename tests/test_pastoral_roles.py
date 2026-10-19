from scripts.check_pastoral_roles import generic_checks,source_checks,integration_checks,attribution_checks,structure

def test_holding_function_and_principality_share_the_same_role():
    assert len(generic_checks()['role_combinations'])==64

def test_the_source_distinguishes_incidental_and_principal_care():
    assert source_checks()['task_content_not_executed']

def test_three_examples_retain_the_same_person_and_conditional_scope():
    assert integration_checks()['ordinary_baseline_agrees']

def test_attribution_does_not_assert_the_role_or_religious_task():
    assert attribution_checks()['all_pastoral_and_task_facts_unknown']

def test_existing_meanings_and_primary_evidence_are_preserved():
    assert structure()['primary_evidence_valid']
