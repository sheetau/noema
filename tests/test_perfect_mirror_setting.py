from scripts.check_perfect_mirror_setting import flow_checks,region_checks,physical_checks,quantifier_checks,presentation_checks,structure_checks

def test_flow():assert flow_checks()['transmission_and_body_transfer_separately_zero']
def test_region():assert region_checks()['all_four_coordinate_slots_bound']
def test_physical():assert physical_checks()['all_66_settings_share_same_physical_model']
def test_quantifiers():assert quantifier_checks()['all_62_existential_roles_share_one_assignment']
def test_presentation():assert presentation_checks()['quoted_contents_not_executed']
def test_structure():assert structure_checks()['all_394_previous_statements_and_meanings_preserved']
