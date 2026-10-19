from scripts.check_written_carriers import generic_checks,multiplicity_checks,source_checks,attribution_checks,structure

def test_the_same_record_connects_work_carrier_and_readability():
    assert len(generic_checks()['record_combinations'])==64

def test_multiple_copies_and_shared_carriers_do_not_collapse_identity():
    assert multiplicity_checks()['shared_carrier_does_not_identify_works']

def test_source_composition_separates_carriers_access_and_task_performance():
    assert source_checks()['task_content_not_executed']

def test_attribution_keeps_work_and_carrier_facts_unknown():
    assert attribution_checks()['all_work_record_and_carrier_facts_unknown']

def test_existing_review_meanings_and_notations_are_preserved():
    assert structure()['removed_primitives']==['sd']
