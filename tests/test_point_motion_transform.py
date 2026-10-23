from scripts.check_point_motion_transform import numeric_checks,binding_checks,bridge_checks,full_scope_checks,candidate_checks,content_checks,structure_checks

def test_numeric():assert numeric_checks()['cases']>0
def test_binding():assert binding_checks()['cases']>0
def test_bridge():assert bridge_checks()['cases']>0
def test_full_scope():assert full_scope_checks()['cases']>0
def test_candidate():assert candidate_checks()['cases']>0
def test_content():assert content_checks()['cases']>0
def test_structure():assert structure_checks()['new_primitives']==0
