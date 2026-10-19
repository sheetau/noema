from scripts.check_conditional_forecast import generic_checks,source_checks,attribution_checks,structure

def test_both_consequences_share_the_antecedent_and_case():
    assert len(generic_checks()['cases'])==256

def test_actual_payment_definitions_keep_forecasts_inside_the_supposition():
    assert source_checks()['ordinary_comparisons']==3

def test_attribution_does_not_assert_payment_or_undertaking():
    assert attribution_checks()['all_payment_and_forecast_facts_unknown']

def test_existing_judgments_and_first_causal_sentence_are_unaffected():
    assert structure()['affected_statements']==[5]
