from scripts.check_delegation_sentence import composition_checks, supply_checks, lexical_gap_checks, attribution_checks, integrity_checks


def test_three_examples_and_the_conclusion_keep_separate_truth_conditions():
    assert len(composition_checks()['combinations']) == 32


def test_provider_recipient_task_and_case_cannot_be_exchanged():
    assert supply_checks()['ordinary_full_premise_agrees']


def test_nonclerical_counselor_is_a_recorded_gap_not_a_completed_translation():
    assert lexical_gap_checks()['current_sp_does_not_distinguish_status']


def test_presentation_keeps_source_facts_unknown():
    assert attribution_checks()['all_service_facts_unknown']


def test_the_whole_sentence_is_bound_without_claiming_completion():
    assert integrity_checks()['unresolved_semantic_gates'] == 1
