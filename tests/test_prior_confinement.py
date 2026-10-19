from scripts import check_prior_confinement as checks


def test_one_onset_covers_the_selected_stage_and_endpoint():
    assert checks.generic_checks()['same_onset_witness_retained']


def test_release_and_reclosure_are_not_one_continuing_episode():
    assert checks.native_checks()['endpoint_conjunction_countermodel']


def test_actual_depiction_uses_the_prior_stage_with_the_same_apparatus():
    assert checks.source_checks()['actual_husbandry_training_apparatus_and_local_confinement_evaluated']


def test_timed_depiction_does_not_assert_world_content():
    assert checks.attribution_checks()['seven_excerpt_statements_evaluated']


def test_only_the_confinement_statement_changes():
    assert checks.structure()['revised_statements']==[36]
