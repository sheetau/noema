from scripts.check_wave_observer_question import rest_checks,point_checks,interval_checks,binding_checks,question_checks,structure_checks

def test_rest():assert rest_checks()['whole_interval_rest_distinguishes_drift_and_return']
def test_point():assert point_checks()['same_time_and_three_ordered_coordinates']
def test_interval():assert interval_checks()['all_times_in_chosen_interval_and_region_guard']
def test_binding():assert binding_checks()['every_observer_wave_process_region_and_calibration_slot_fixed']
def test_question():assert question_checks()['two_field_answers_keep_all_preselected_question_parameters']
def test_structure():assert structure_checks()['all_366_statements_and_prior_meanings_preserved']
