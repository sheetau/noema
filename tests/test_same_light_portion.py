from scripts.check_same_light_portion import transport_checks,physical_checks,quantifier_checks,presentation_checks,reading_checks,structure_checks


def test_transport():assert transport_checks()['pointwise_density_not_only_total_preserved']
def test_physical():assert physical_checks()['all_26_physical_roles_shared']
def test_quantifiers():assert quantifier_checks()['all_65_context_roles_bound']
def test_presentation():assert presentation_checks()['can_describe_distinct_from_must_follow_and_unqualified_truth']
def test_reading():assert reading_checks()['cross_unit_prose_characters']==242
def test_structure():assert structure_checks()['all_388_statements_and_judgments_preserved']
