from scripts.check_government_principle_profile import adoption_checks,profile_checks,scope_checks,wrapper_checks,structure_checks

def test_institution_and_opaque_adoption():assert adoption_checks()
def test_content_class_changes():assert profile_checks()
def test_full_scope_and_assessment():assert scope_checks()
def test_content_wrapper():assert wrapper_checks()
def test_structure():assert structure_checks()
