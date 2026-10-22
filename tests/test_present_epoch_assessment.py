from scripts.check_present_epoch_assessment import frame_checks,collective_checks,fixed_dialogue_checks,quality_binding_checks,structure_checks


def test_present_population_is_complete_and_excludes_other_times():
    assert not frame_checks()['complete_current_population']['omit_living']


def test_assessment_attainment_and_progress_remain_separate():
    assert collective_checks()['combinations']==128


def test_question_and_answer_keep_the_same_fixed_present():
    assert fixed_dialogue_checks()['outer_point_does_not_rebind_present']


def test_qualified_ability_keeps_its_own_task_and_reference():
    assert quality_binding_checks()['quality_descriptions_not_executed']


def test_existing_meanings_and_authoritative_manuscript_are_preserved():
    assert structure_checks()['main_statements_preserved']==108
