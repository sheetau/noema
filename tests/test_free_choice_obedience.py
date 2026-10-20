from scripts import check_free_choice_obedience as checks


def test_every_topic_and_extent_pair_needs_an_unprohibited_candidate():
    assert checks.permission_checks()['independent_topic_extent_pairs']


def test_obedience_requires_coverage_fulfillment_and_guidance():
    assert checks.obedience_checks()['mere_coincidence_is_not_guided_obedience']


def test_permission_does_not_depend_on_actual_obedience():
    assert checks.group_checks()['permission_not_conditioned_on_actual_obedience']


def test_ranked_quote_does_not_evaluate_norms_or_execution():
    assert checks.quotation_checks()['reference_norms_execution_and_guidance_unknown']


def test_reused_libraries_and_old_judgments_are_preserved():
    assert checks.structure_checks()['preserved_reviewed_sentence_characters'] == 366
