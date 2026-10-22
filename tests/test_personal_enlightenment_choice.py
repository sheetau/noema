from scripts.check_personal_enlightenment_choice import duty_checks,goal_checks,temporal_checks,choice_checks,structure_checks

def test_all_owed_items_are_mapped_without_requiring_knowledge_success():
    assert duty_checks()['native_complete_duty_mapping']['unmapped_duty']==[False,False]

def test_inquiry_requires_same_person_activity_topic_and_unexecuted_goal():
    assert sum(goal_checks()['native_inquiry_execution_and_goal'].values())==1

def test_pause_excludes_end_but_resumption_includes_it():
    assert temporal_checks()['native_temporal_quantification']['end']==[False,True,True]

def test_deferral_and_renunciation_are_distinct_actual_choices():
    assert choice_checks()['distinct_deferred_and_renounced_choices']['both']==[False,False]

def test_imported_meanings_and_all_notations_are_preserved():
    assert structure_checks()['preserved_main_statements']==104
