from scripts.check_delegation_reading import supply_checks, appointment_checks, attribution_checks, integrity_checks


def test_supply_bindings_in_the_corrected_full_sentence():
    assert supply_checks()['ordinary_full_premise_agrees']


def test_the_previous_nonappointed_countermodel_is_resolved():
    assert appointment_checks()['prior_nonappointed_countermodel_excluded']


def test_the_hypothetical_presentation_keeps_facts_independent():
    assert attribution_checks()['institutional_and_action_facts_unknown']


def test_the_review_has_exact_sentence_scope_and_retains_its_predecessor():
    assert integrity_checks()['reviewed_sentence_characters'] == 157
