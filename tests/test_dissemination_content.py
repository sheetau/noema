from scripts import check_dissemination_content as checks


def test_recipient_state_preserves_appraisal_norm_and_qualitative_disposition():
    assert checks.state_checks()['contextual_referents_preserved_in_norm_description']


def test_bound_forecast_fields_share_context_and_reject_wrong_quote_referents():
    assert checks.binding_checks()['all_eight_providers_bound']


def test_topic_and_message_are_local_existential_witnesses_without_enumeration():
    assert checks.witness_checks()['same_person_and_opportunity']


def test_earlier_reviewed_text_and_native_dissemination_body_are_preserved():
    assert checks.structure_checks()['preserved_whole_unit_reviews'] == 13
