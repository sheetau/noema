from scripts import check_walking_acquisition as checks


def test_walking_capacity_keeps_task_basis_and_assessment_distinctions():
    assert checks.capacity_checks()['unknown_inputs_refused']==7


def test_same_bodily_experiences_contribute_to_same_capacity_change():
    assert checks.acquisition_checks()['same_person_experiences_process_and_endpoints']


def test_bodily_prospect_is_future_scoped_and_independent_of_intellectual_content():
    assert len(checks.prospect_checks()['independent_contents'])==4


def test_depiction_quotes_the_whole_prospect_without_asserting_actual_learning():
    assert checks.attribution_checks()['all_world_contents_unknown']


def test_existing_reviewed_contents_and_three_notations_are_preserved():
    assert checks.structure()['preserved_reviewed_sentence_characters']==1021
