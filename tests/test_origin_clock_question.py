from scripts.check_origin_clock_question import local_checks,binding_checks,capability_checks,origin_checks,comparison_checks,rate_checks,presentation_checks,structure_checks

def test_local_candidates_and_calibration():assert local_checks()['all_display_readings_match_current_coordinates']
def test_shared_witnesses():assert binding_checks()['shared_four_and_five_witnesses_every_slot']
def test_separate_rest_capabilities():assert capability_checks()['separate_permitted_frame_capabilities_not_simultaneous_actual_rest']
def test_current_origin():assert origin_checks()['all_local_candidates_at_same_origin']
def test_same_event_comparison():assert comparison_checks()['same_actual_event_current_coordinates_and_representative_path']
def test_rate_all_pairs():assert rate_checks()['all_record_pairs_not_one_selected_pair']
def test_open_question_and_source_order():assert presentation_checks()['question_has_no_preset_rate_or_existence_claim']
def test_preservation_and_source():assert structure_checks()['prior_whole_unit_judgments_preserved']
