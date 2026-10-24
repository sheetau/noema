from scripts.check_mirror_surface_pressure import plane_checks,mapping_checks,patch_checks,pressure_checks,setting_question_checks,structure_checks

def test_plane():assert plane_checks()['containment_and_complete_plane_coverage_distinguished']
def test_mapping():assert mapping_checks()['every_counterpart_and_all_record_pairs_required']
def test_patch():assert patch_checks()['proper_nonempty_rectangular_material_patch']
def test_pressure():assert pressure_checks()['mean_normal_force_over_same_positive_area_and_duration']
def test_question():assert setting_question_checks()['all_setting_roles_captured_before_answer']
def test_structure():assert structure_checks()['all_394_statements_and_judgments_preserved']
