from scripts.check_royal_intervention_sentence import general_content_checks,evaluative_depiction_checks,adapter_checks,discourse_checks,structure_checks


def test_general_contents_use_one_reference_without_rewriting_conditions():
    assert len(general_content_checks()['same_general_reference'])==5


def test_bare_scrutiny_and_evaluative_depiction_share_the_same_event():
    assert evaluative_depiction_checks()['same_event_without_approval']['h26im']==[True,False]


def test_support_extent_and_quotation_keep_exact_case_and_argument_bindings():
    assert adapter_checks()['literal_and_contextual_application_separate']


def test_presentation_rejects_missing_or_misbound_relations_without_executing_truth():
    assert discourse_checks()['quoted_truth_not_executed']


def test_complete_reading_preserves_all_existing_statements_and_reviews():
    assert structure_checks()['new_reviewed_sentence_characters']==435
