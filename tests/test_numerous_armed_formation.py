from scripts import check_numerous_armed_formation as check


def test_institution_assignment_command_and_current_members():check.formation_checks()
def test_same_real_readiness_and_military_identity():check.readiness_checks()
def test_exact_membership_and_fixed_numerosity():check.count_checks()
def test_same_witnesses_for_the_complete_group_conditions():check.connection_checks()
def test_legacy_declarations_meanings_and_source_provenance():check.structure_checks()
