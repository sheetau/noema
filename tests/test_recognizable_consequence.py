from scripts.check_recognizable_consequence import generic_checks, scope_checks, source_truth_checks, structure


def test_recognizable_presentation_is_independent_of_the_presented_facts():
    assert len(generic_checks()['independent_truth_combinations']) == 16


def test_marker_retains_author_node_context_premise_and_consequence():
    assert scope_checks()['all_world_facts_unknown']


def test_the_actual_conditional_can_be_false_when_presented_as_recognizable():
    assert source_truth_checks()['ordinary_countermodel_agrees']


def test_new_statement_preserves_every_old_meaning_and_review():
    assert structure()['all_old_meanings_unchanged']
