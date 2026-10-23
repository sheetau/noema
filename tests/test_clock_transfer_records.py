from scripts.check_clock_transfer_records import local_checks,binding_checks,rate_checks,path_checks,rest_checks,setup_checks,structure_checks

def test_local_current_displays():assert local_checks()['all_alternative_readings_unique']
def test_shared_display_witnesses():assert binding_checks()['time_and_reading_not_separate_witnesses']
def test_complete_rate_phase():assert rate_checks()['real_time_quantifier_preserved']
def test_complete_straight_path():assert path_checks()['endpoint_only_detours_and_nonuniform_progress_rejected']
def test_representative_rest():assert rest_checks()['initial_and_motion_phases_are_separate']
def test_same_transfer_setup():assert setup_checks()['initial_sync_straight_motion_and_same_arrival_bound']
def test_transfer_dependency_preservation():assert structure_checks()['preserved_statements']==343
