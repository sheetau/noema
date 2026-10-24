from scripts.check_electron_comoving_history import frame_checks,map_checks,history_checks,derivative_checks,source_checks,structure_checks

def test_frames():assert frame_checks()
def test_bidirectional_maps():assert map_checks()
def test_full_history_bindings():assert history_checks()
def test_native_coordinate_derivatives():assert derivative_checks()
def test_current_electron_and_rest():assert source_checks()
def test_structure():assert structure_checks()
