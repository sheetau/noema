from scripts import check_public_first_sentence as checks


def test_factoring_preserves_the_combined_claim_and_scope_failures():
    assert checks.factoring_checks()['same_combined_claim']


def test_condition_goal_and_qualification_keep_the_same_contextual_inputs():
    assert checks.family_checks()['shared_condition_goal_and_qualification']


def test_discourse_preserves_attribution_order_axis_and_modal_qualification():
    assert checks.discourse_checks()['clause_order_author_axis_and_qualification_preserved']


def test_presentation_relations_accept_non_kant_contents_without_running_them():
    assert checks.portability_checks()['world_truth_independent']


def test_first_sentence_review_preserves_the_thirteen_earlier_whole_unit_reviews():
    assert checks.structure_checks()['preserved_whole_unit_reviews'] == 13
