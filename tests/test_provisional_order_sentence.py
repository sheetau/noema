from scripts.check_provisional_order_sentence import generic_checks,projection_checks,frame_checks,discourse_checks,structure_checks


def test_generic_people_have_possible_configurations_not_all_laws_licensed():
    r=generic_checks();assert not r['generic_people_existential_eight_target_configuration']['missing_second']
    assert r['different_peoples_need_not_share_law_or_configuration']


def test_same_people_and_law_are_projected_to_the_previous_question():
    r=projection_checks();assert all(r['lifted_question_equals_prior_question_for_both_answers'].values())


def test_qualified_possibility_depiction_and_public_cognitive_agency_keep_frame():
    r=frame_checks();assert r['expectation_keeps_same_ten_objects_candidate_and_start']


def test_all_discourse_is_bound_to_one_whole_author_without_world_execution():
    r=discourse_checks();assert sum(r['one_whole_author_anaphora_qualification_depiction_and_all_discourse'].values())==1
    assert r['quoted_world_not_executed']


def test_whole_sentence_reading_preserves_old_judgments_and_roundtrips():
    r=structure_checks();assert (r['preserved_statements'],r['added_statements'],r['new_reviewed_sentence_characters'])==(102,1,747)
    assert r['literal_expectation_and_physical_throne_absent_from_world_conditions']
