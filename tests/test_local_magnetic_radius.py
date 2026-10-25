from scripts import check_local_magnetic_radius as check

def test_both_printed_formulas():assert check.numeric_checks()
def test_only_magnetic_normal_action():assert check.exclusive_checks()
def test_actual_calibrated_physics():assert check.physical_checks()
def test_geometric_radius_and_units():assert check.geometry_checks()
def test_shared_case_and_equivalence():assert check.connection_checks()
def test_full_source_presentation():assert check.presentation_checks()
def test_source_and_preserved_structure():assert check.structure_checks()
