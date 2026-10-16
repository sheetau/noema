from scripts import check_definition_question as check


def test_candidate_check_preserves_every_person_and_situation():
    result=check.checks()
    assert result['property_profile_pairs']==256 and result['isolated_person_scene_differences']==8
    assert result['unlowered_uncached_cases']==2


def test_wrong_answer_can_be_attributed_without_becoming_true():
    result=check.checks()
    assert result['presentation_combinations']==32
    for rows in result['question_answer_checks'].values():
        assert rows['correct']==[True]*6
        assert rows['attributed_wrong_answer']==[False,False,True,True,True,False]


def test_source_question_and_answer_use_the_same_author_context_and_reference():
    rows=check.checks()['source_contrasts']
    assert rows['baseline']==[True]
    for name in ('other_question_node','other_answer_node','other_author','other_context','different_reference','different_answer'):
        assert rows[name]==[False]


def test_response_direction_order_and_distinct_nodes_are_preserved():
    rows=check.checks()['source_contrasts']
    for name in ('missing_presentation','missing_definition','reverse_order','reverse_response','same_node'):
        assert rows[name]==[False]


def test_question_construction_and_attribution_do_not_execute_the_answer():
    result=check.checks()
    assert result['nonfactive_question_and_answer_presentation'] and result['unknown_answer_refused']


def test_infinite_description_domain_and_wrong_quote_rank_are_not_silently_accepted():
    result=check.checks()
    assert 'description domain' in result['unbounded_answer_enumeration_refused']
    assert result['wrong_candidate_rank_refused']


def test_existing_manuscript_is_preserved_and_title_framing_is_added():
    result=check.structure()
    assert result['inherited_basis_checked'] and result['previous_declarations_preserved']
    assert result['previous_statements_preserved']==15 and result['new_attribution_statements']==1
    assert result['new_definitions']==5 and result['new_primitives']==2


def test_alignment_identifies_the_title_and_the_existing_opening_definition():
    rows=check.alignment()['segments']
    assert [r['unit'] for r in rows]==['kant-1784:u0005','kant-1784:u0006','kant-1784:u0008']
    assert rows[0]['source']=='Beantwortung der Frage:' and rows[1]['source']=='Was ist Aufklärung?'
    assert rows[2]['source'].startswith('Aufklärung ist der Ausgang')
