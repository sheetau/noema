from scripts.check_electron_comoving_equations import transform_checks,binding_checks,initial_checks,presentation_checks,binder_checks,structure_checks

def test_transforms():assert transform_checks()
def test_connections():assert binding_checks()
def test_initial():assert initial_checks()
def test_presentation():assert presentation_checks()
def test_binders():assert binder_checks()
def test_structure():assert structure_checks()
