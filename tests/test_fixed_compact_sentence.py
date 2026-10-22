from scripts.check_fixed_compact_sentence import generic_checks,adapter_checks,lifetime_checks,depiction_checks,discourse_checks,structure_checks

def test_all_compacts_are_prohibited_without_selecting_harmful_success():
    assert sum(generic_checks()['all_candidates_fixed_source_role_reference_and_first_consequence'].values())==2

def test_six_object_adapters_preserve_same_compact_and_period():
    assert len(adapter_checks()['exact_six_adapters'])==4

def test_even_one_lifetime_is_a_subset_not_a_replacement():
    assert lifetime_checks()['native_lifetime_subset']['split_lifetimes']==[True,False]

def test_literal_disappearance_requires_same_object_and_cause():
    assert sum(depiction_checks()['native_literal_disappearance_and_same_cause'].values())==1

def test_all_discourse_keeps_same_whole_and_tentative_harm():
    assert sum(discourse_checks()['same_whole_author_reference_and_qualified_presentation'].values())==1

def test_complete_sentence_preserves_all_prior_judgments():
    assert structure_checks()['new_reviewed_sentence_characters']==320
