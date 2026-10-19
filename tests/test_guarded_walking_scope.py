from scripts import check_guarded_walking_scope as checks


def test_compound_claim_keeps_recipients_events_and_prior_stages():
    assert checks.compound_checks()['one_person_success_does_not_replace_all_recipients']


def test_late_confinement_does_not_establish_confinement_at_prevention():
    assert checks.confinement_checks()['independent_past_witnesses_do_not_establish_overlap']


def test_unknown_facts_are_not_invented():
    assert checks.unknown_checks()['unknown_inputs_refused'] == 5


def test_current_manuscript_and_prior_reviews_are_preserved():
    assert checks.structure()['preserved_review_selections'] == 11
