from scripts.check_civic_human_agency import native_capacity_checks,population_checks,family_checks,structure_checks

def test_native_capacity_and_passive_role():assert native_capacity_checks()
def test_full_population():assert population_checks()
def test_same_person_and_point():assert family_checks()
def test_structure():assert structure_checks()
