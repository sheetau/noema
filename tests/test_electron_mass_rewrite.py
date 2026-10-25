from scripts.check_electron_mass_rewrite import equation_checks,coordinate_checks,connection_checks,presentation_checks,binder_checks,structure_checks

def test_six_equalities():assert equation_checks()
def test_corresponding_event():assert coordinate_checks()
def test_same_settings():assert connection_checks()
def test_rewrite_presentation():assert presentation_checks()
def test_all_binders():assert binder_checks()
def test_preserved_structure():assert structure_checks()
