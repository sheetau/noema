from scripts import check_prejudice_reason as checks


def test_harm_reuses_the_same_native_causal_chain():
    assert checks.harm_checks()['exact_existing_causal_chain_projection']


def test_degree_does_not_replace_harm_or_change_case_scope():
    assert checks.degree_checks()['degree_never_replaces_actual_harm']


def test_degree_is_of_the_same_whole_case_and_target_domain():
    assert checks.family_checks()['degree_applies_to_whole_case_not_each_person']


def test_demonstrative_degree_and_reason_keep_their_direction_and_quotation():
    assert checks.discourse_checks()['all_world_inputs_unknown_without_execution']


def test_inherited_meanings_and_reviews_survive():
    assert checks.structure_checks()['inherited_meanings_unchanged']
