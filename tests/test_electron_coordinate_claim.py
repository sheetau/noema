from scripts.check_electron_coordinate_claim import connection_checks,presentation_checks,binder_checks,structure_checks

def test_connections():assert connection_checks()
def test_presentation():assert presentation_checks()
def test_binders():assert binder_checks()
def test_structure():assert structure_checks()
