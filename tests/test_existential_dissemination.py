from scripts.check_existential_dissemination import native_checks, boundary_checks, closed_content_checks, structure


def test_native_routes_preserve_causal_temporal_and_person_bindings():
    assert len(native_checks()['contrasts'])==15


def test_unknowns_and_infinite_domains_are_not_filled_in():
    assert boundary_checks()['unknown_inputs_refused']==4


def test_shared_departure_scope_and_existing_reviews_are_preserved():
    assert structure()['departure_witnesses_shared_outside_recipient_scope']


def test_existential_content_is_quotable_inside_the_freedom_condition():
    assert closed_content_checks()['closed_ranked_attribution_without_world_evaluation']
