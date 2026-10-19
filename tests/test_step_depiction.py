from scripts import check_step_depiction as checks


def test_extracted_target_is_in_the_existing_prior_stage():
    assert checks.embedding_checks()['abstract_conjunction_law'][0]['status']=='valid'


def test_target_prevention_and_permission_share_the_prior_point():
    result=checks.target_checks()
    assert len(result['contrasts'])==7 and result['separate_past_witnesses_do_not_form_a_shared_point']


def test_bodily_permission_covers_all_four_shapes_at_same_point():
    assert len(checks.body_checks()['combinations'])==16


def test_timed_depiction_keeps_world_contents_quoted():
    assert checks.attribution_checks()['five_excerpt_statements_executed']


def test_preserved_meanings_and_roundtrips():
    assert checks.structure()['preserved_review_selections']==11
