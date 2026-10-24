from scripts.check_electrodynamic_part_heading import heading_checks,topic_checks,structure_checks


def test_heading():assert heading_checks()['same_paper_parent_and_distinct_first_part']
def test_topic():assert topic_checks()['charge_transport_electric_and_magnetic_roles_shared']
def test_structure():assert structure_checks()['heading_not_an_assertion_of_physics_or_goal_completion']
