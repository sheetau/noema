from scripts.check_velocity_composition_claim import numeric_checks,physical_checks,chain_checks,presentation_checks,structure_checks


def test_numeric():assert numeric_checks()['cases']>0
def test_physical():assert physical_checks()['cases']>0
def test_chain():assert chain_checks()['cases']>0
def test_presentation():assert presentation_checks()['cases']>0
def test_structure():assert structure_checks()['other_statements_preserved']==353
