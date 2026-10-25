from scripts import check_traversed_potential as check

def test_printed_signed_formula():assert check.numeric_checks()
def test_physical_quotient_units():assert check.unit_checks()
def test_whole_traversed_path():assert check.path_checks()
def test_same_process_and_energy():assert check.connection_checks()
def test_second_item_and_inference():assert check.presentation_checks()
def test_preserved_source_and_structure():assert check.structure_checks()
