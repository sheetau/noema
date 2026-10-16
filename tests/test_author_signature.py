from scripts import check_author_signature as check


def test_name_use_alone_does_not_establish_author_credit():
    assert check.checks()['condition_combinations']==16


def test_same_act_name_referent_document_and_context_are_required():
    rows=check.checks()['source_contrasts'];assert rows['baseline']==[True]
    assert all(v==[False] for n,v in rows.items() if n!='baseline')


def test_presenter_can_be_an_editor_and_name_is_not_the_person():
    result=check.checks();assert result['presenter_may_differ_from_credited_author']
    assert result['source_contrasts']['name_is_person']==[False]
    assert result['original_paragraph_context_not_used'] and result['unlowered_uncached']


def test_unknown_assignment_or_author_credit_is_not_inferred_from_spelling():
    assert check.checks()['unknown_assignment_and_credit_refused']


def test_manuscript_is_extended_without_reinterpreting_prior_declarations():
    result=check.structure()
    assert result['previous_statement_syntax_preserved']==16 and result['new_statements']==1
    assert result['new_primitives']==6 and result['new_definitions']==2
    assert result['annotations_belong_to_name_not_person']


def test_source_association_preserves_editorial_expansion():
    row=check.alignment()['segments'][0]
    assert row['unit']=='kant-1784:u0018' and row['source']=='I.[mmanuel] Kant.'
    assert row['range']==[0,len(row['source'])]
