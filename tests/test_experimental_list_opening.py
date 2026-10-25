from scripts import check_experimental_list_opening as check

def test_three_properties_and_shared_premises():assert check.content_checks()
def test_generic_intention_to_enumerate():assert check.enumeration_checks()
def test_full_source_roles_and_references():assert check.presentation_checks()
def test_source_and_preserved_evidence():assert check.structure_checks()
