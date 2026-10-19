from scripts import check_generalized_deterrence as checks


def test_case_normality_keeps_incomparable_cases_and_refuses_bad_orders():
    assert checks.generic_checks()['strict_orders']==19


def test_generic_intimidation_and_avoidance_frequency_have_distinct_scopes():
    assert checks.source_checks()['atypical_fear_cases_remain_in_frequency_population']


def test_author_and_expectation_bind_the_new_joint_claim_without_asserting_it():
    assert checks.attribution_checks()['world_contents_unknown']


def test_current_judgments_and_three_notations_survive_the_single_statement_revision():
    assert checks.structure()['changed_statement_indices']==[37]
