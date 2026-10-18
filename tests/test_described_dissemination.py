from scripts.check_described_dissemination import attribution_checks,content_checks,binding_checks,rank_and_unknown_checks,structure


def test_attribution_uses_closed_content_without_running_unknown_world_facts():
    assert attribution_checks()['all_world_facts_unknown_but_attribution_evaluated']


def test_attribution_and_native_future_content_can_differ_in_truth():
    assert content_checks()['appointment_thinking_departure_and_relative_transmission_bodies_executed']


def test_providers_use_the_same_person_opportunity_and_recipient():
    assert binding_checks()['person_and_opportunity_provider_bindings']==13


def test_quote_ranks_and_unknown_inputs_are_not_silently_coerced():
    assert rank_and_unknown_checks()['invalid_rank_uses_refused']==2


def test_existing_meanings_statements_and_reviews_are_preserved():
    assert structure()['new_primitive_signatures']==1
