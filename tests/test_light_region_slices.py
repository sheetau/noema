from scripts.check_light_region_slices import geometry_checks,physical_checks,binding_checks,volume_checks,structure_checks

def test_geometry():assert geometry_checks()['inverse_map_includes_time']
def test_physical():assert physical_checks()['same_portion_wave_process_scope_and_units_in_both_frames']
def test_binding():assert binding_checks()['all_18_roles_bound']
def test_volume():assert len(volume_checks()['equal_volume_at_nonzero_speed'])==2
def test_structure():assert structure_checks()['all_386_statements_and_judgments_preserved']
