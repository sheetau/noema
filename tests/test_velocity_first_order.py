from scripts.check_velocity_first_order import numeric_checks,derivative_checks,bridge_checks,quantifier_checks,structure_checks


def test_numeric():assert numeric_checks()['cases']>0
def test_derivative():assert derivative_checks()['cases']>0
def test_bridge():assert bridge_checks()['cases']>0
def test_quantifiers():assert quantifier_checks()['cases']>0
def test_structure():assert structure_checks()['new_primitives']==0
