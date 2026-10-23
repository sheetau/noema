from scripts import check_first_principle as c

def test_numeric():assert c.numeric_checks()
def test_point_bindings():assert c.point_binding_checks()
def test_frames():assert c.frame_checks()
def test_laws():assert c.law_checks()
def test_scope():assert c.scope_checks()
def test_presentation():assert c.presentation_checks()
def test_structure():assert c.structure_checks()
