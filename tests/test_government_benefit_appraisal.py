from scripts.check_government_benefit_appraisal import comparison_checks,completeness_checks,concrete_policy_checks,institutional_checks,nonfactivity_checks,structure_checks

def test_comparative_prospects():assert comparison_checks()
def test_complete_assessed_scopes():assert completeness_checks()
def test_same_concrete_policy():assert concrete_policy_checks()
def test_institutional_judgment():assert institutional_checks()
def test_nonfactive_appraisal():assert nonfactivity_checks()
def test_structure():assert structure_checks()
