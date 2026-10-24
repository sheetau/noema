from scripts.check_parallel_current_records import numeric_checks,record_checks,geometry_checks,scope_checks,structure_checks

def test_numeric():assert numeric_checks()['beta_uses_composed_speed']
def test_records():assert record_checks()['nonempty_complete_scope_and_value_uniqueness']
def test_geometry():assert geometry_checks()['all_twelve_origin_coordinates_checked']
def test_scope():assert scope_checks()['all_four_universal_slots_bound']
def test_structure():assert structure_checks()['other_statements_preserved']==354
