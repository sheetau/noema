from scripts.check_electron_coordinate_normalization import rotation_checks,map_checks,history_checks,boost_checks,physical_checks,structure_checks
def test_rotations():assert rotation_checks()
def test_maps():assert map_checks()
def test_histories():assert history_checks()
def test_boosts():assert boost_checks()
def test_physical_charts():assert physical_checks()
def test_structure():assert structure_checks()
