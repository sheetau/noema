from scripts.check_vacuum_light_postulate import local_checks,speed_checks,scope_checks,frame_checks,structure_checks

def test_bound_light_interval_and_local_clocks():assert local_checks()['native_local_time_and_speed']
def test_exact_speed_and_unsampled_reals():assert speed_checks()['full_real_domain_refused']
def test_complete_nonempty_scope():assert scope_checks()['one_bad_selected_case_rejected']
def test_common_speed_in_all_qualified_frames():assert frame_checks()['same_V_and_context']
def test_preserved_manuscript_and_readings():assert structure_checks()['no_new_author_assertion']
