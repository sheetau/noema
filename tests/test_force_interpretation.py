from scripts.check_force_interpretation import electric_checks,premise_checks,wording_checks,presentation_checks,structure_checks

def test_electric():assert electric_checks()['magnetic_transform_not_added']
def test_premise():assert premise_checks()['unit_amounts_and_conditional_force_contents_shared']
def test_wording():assert wording_checks()['two_distinct_wordings_same_target_and_interpretation']
def test_presentation():assert presentation_checks()['mithin_and_following_first_second_items']
def test_structure():assert structure_checks()['original_358_statements_preserved']
