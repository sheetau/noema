from scripts.check_collective_change import generic_checks,source_checks,structure


def test_exact_population_and_change_scopes():
    assert generic_checks()['membership_and_transition_combinations']==64


def test_one_plural_and_all_native_changes_are_distinct():
    result=source_checks()
    assert result['cases']['one']['values']==[True,False,False]
    assert result['cases']['two']['values']==[True,True,False]
    assert result['cases']['all']['values']==[True,True,True]


def test_existing_meanings_and_reviews_are_preserved():
    assert structure()['reviewed_statement_bindings_preserved']==7
