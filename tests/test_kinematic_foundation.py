from scripts.check_kinematic_foundation import referent_checks,claim_checks,scope_checks,sentence_checks,structure_checks

def test_physical_reference_roles_and_unbounded_history():assert referent_checks()['full_real_history_domain_refused']
def test_all_claims_keep_the_same_physical_interpretation():assert claim_checks()['all_claims_and_consequences']
def test_upcoming_and_every_other_electrodynamics():assert scope_checks()['every_other_electrodynamics']
def test_same_project_inquiry_and_explanatory_direction():assert sentence_checks()['both_contents_and_explanatory_direction']
def test_preserved_judgments_and_whole_first_sentence():assert structure_checks()['prior_reviews_preserved']
