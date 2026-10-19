from scripts.check_book_form import generic_checks, source_checks, integration_checks, attribution_checks, structure


def test_record_and_carrier_form_share_the_same_witnesses():
    assert len(generic_checks()['relation_combinations']) == 256


def test_source_accepts_actual_or_planned_form_but_requires_a_record():
    assert source_checks()['task_content_not_executed']


def test_conditional_example_retains_its_nonvacuous_premise_check():
    assert integration_checks()['ordinary_baseline_agrees']


def test_authorial_attribution_does_not_assert_a_book_or_production_plan():
    assert attribution_checks()['all_carrier_form_and_plan_facts_unknown']


def test_existing_reviews_and_conscience_components_remain_unchanged():
    assert structure()['conscience_components_unchanged']
