from scripts.check_dignity_conforming_treatment import standing_checks,public_dealing_checks,treatment_checks,adoption_checks,structure_checks

def test_non_substitutable_standing():assert standing_checks()
def test_actual_public_dealings():assert public_dealing_checks()
def test_complete_treatment_policy():assert treatment_checks()
def test_exact_adoption_and_fulfillment():assert adoption_checks()
def test_structure():assert structure_checks()
