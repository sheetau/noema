from scripts import check_second_principle as c

def test_numeric():assert c.numeric_checks()
def test_time():assert c.time_checks()
def test_emission():assert c.emission_checks()
def test_physical():assert c.physical_checks()
def test_scope():assert c.scope_checks()
def test_presentation():assert c.presentation_checks()
def test_structure():assert c.structure_checks()
