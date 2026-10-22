from scripts.check_salvation_work_protection import capacity_checks,work_checks,candidate_checks,violence_checks,universal_checks,prevention_checks,adapter_checks,structure_checks

def test_full_capacity_requires_unique_greatest_actual_effort():
    rows=capacity_checks()['native_full_capacity']
    assert rows['full'] and not rows['below_capacity'] and not rows['ambiguous_measurement']

def test_work_requires_both_aims_but_neither_success():
    assert work_checks()['work_does_not_require_either_success']

def test_candidates_do_not_require_previous_necessity_belief_or_execution():
    assert candidate_checks()['native_candidate_without_success_or_necessity_belief']['baseline']

def test_violent_hindrance_does_not_depend_on_victim_success_or_failure():
    assert violence_checks()['hindrance_then_actual_target']==[[True,False],[True,True]]
    assert not violence_checks()['native_violent_hindrance']['justified_force']

def test_protection_covers_both_orders_of_subject_pairs():
    rows=universal_checks()['every_distinct_subject_pair_and_candidate']
    assert not rows['first_victim_hindered'] and not rows['second_victim_hindered']

def test_preventive_duty_requires_remit_and_requirement_without_actual_success():
    assert prevention_checks()['duty_does_not_execute_prevention']

def test_protection_and_work_adapters_preserve_positions_and_ranks():
    assert adapter_checks()['exact_adapters']['r5ob']==[0,1,2]

def test_existing_main_and_evidence_preserved():
    assert structure_checks()['preserved_main_statements']==106
