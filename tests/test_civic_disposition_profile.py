from scripts.check_civic_disposition_profile import disposition_checks,inventory_checks,distance_checks,trajectory_checks,structure_checks

def test_native_dispositions():assert disposition_checks()
def test_fixed_inventory():assert inventory_checks()
def test_weighted_distance():assert distance_checks()
def test_trajectory():assert trajectory_checks()
def test_structure():assert structure_checks()
