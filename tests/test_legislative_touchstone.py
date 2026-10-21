from scripts.check_legislative_touchstone import permission_checks,adoption_checks,binding_checks,criterion_checks,discourse_checks,structure_checks

def test_general_actor_permission_and_exact_target():
    r=permission_checks();assert sum(r['permission_conflict_table'].values())==1
    assert not any(r['exact_actor_and_four_targets'].values()) and r['quoted_adoption_not_executed']

def test_general_adoption_and_self_adoption_remain_distinct():
    r=adoption_checks();rows=r['native_general_adoption_and_self_difference']
    assert rows['actor']==[True,False] and rows['people']==[True,True] and rows['split_witness']==[False,False]
    assert r['no_definition_boundaries']

def test_all_binding_positions_and_lengths():
    r=binding_checks();assert {k:(len(v),sum(v)) for k,v in r['exact_positions'].items()}=={'r5ev':(16,4),'r5ey':(9,3),'r5ez':(9,3)}
    assert r['wrong_lengths_rejected']

def test_complete_two_way_criterion_for_every_frame():
    r=criterion_checks();assert len(r['two_independent_law_frames'])==64
    assert r['necessary_and_sufficient_not_just_necessary'] and not any(r['mixed_tuple_failures'])

def test_same_question_deliberative_tone_metaphor_and_author():
    r=discourse_checks();assert sum(r['whole_criterion_question_deliberation_metaphor_and_order'].values())==1
    assert r['questions_norms_enactment_and_literal_stone_not_executed']

def test_prior_reviews_and_new_full_sentence_selection():
    r=structure_checks();assert (r['preserved_statements'],r['added_statements'],r['new_reviewed_sentence_characters'])==(101,1,144)
    assert (r['new_definitions'],r['new_primitives'])==(8,10)
