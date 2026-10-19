from scripts import check_fear_proneness as checks


def test_fear_proneness_is_independent_of_present_fear_and_courage():
    assert checks.disposition_checks()['current_fear_and_courage_independent_of_disposition']


def test_cause_targets_the_same_disposition_not_an_old_actual_state():
    assert checks.causal_checks()['old_actual_state_not_accepted_as_causal_result']


def test_person_disposition_and_general_case_and_frequency_scopes_remain_distinct():
    assert checks.integration_checks()['person_disposition_case_generality_and_population_frequency_distinct']


def test_author_and_expectation_bind_the_new_claim_without_asserting_world_truth():
    assert checks.attribution_checks()['world_contents_unknown']


def test_reviewed_selections_and_three_notations_survive_the_revision():
    assert checks.structure()['changed_statement_indices']==[37]
