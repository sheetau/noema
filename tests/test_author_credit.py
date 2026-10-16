from scripts import check_author_credit as check


def test_three_relations_are_required_without_a_presenter():
    result=check.checks()
    assert result['condition_combinations']==8 and result['new_does_not_evaluate_presenter']
    assert result['old_requires_author_as_presenter']


def test_name_subject_act_document_and_context_cannot_be_swapped():
    rows=check.checks()['source_contrasts']
    assert rows['baseline']==[True] and all(v==[False] for k,v in rows.items() if k!='baseline')


def test_unknown_name_assignment_and_credit_are_not_guessed():
    assert check.checks()['unknown_assignment_and_credit_refused']


def test_only_author_credit_definition_is_revised():
    result=check.structure()
    assert result['changed_definition']=='hzil' and result['previous_statements_preserved']==17
    assert result['new_primitives']==0 and result['identifier_forms_on_name_object']


def test_facsimile_provenance_and_electronic_expansion_are_separate():
    record,unit=check.source_check()
    assert record['electronic_transcription']=='I.[mmanuel] Kant.'
    assert record['adopted_reading']=='I. Kant.'
    assert unit['id']=='kant-1784:u0018'
