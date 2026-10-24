from scripts.check_electron_transformed_dynamics import equation_checks,history_checks,connection_checks,law_checks,presentation_checks,binder_checks,structure_checks

def test_equations():assert equation_checks()
def test_histories():assert history_checks()
def test_connections():assert connection_checks()
def test_law():assert law_checks()
def test_presentation():assert presentation_checks()
def test_binders():assert binder_checks()
def test_structure():assert structure_checks()
