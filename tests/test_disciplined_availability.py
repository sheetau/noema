from scripts import check_disciplined_availability as check


def test_nonempty_commands_on_actual_military_roles():check.roles_checks()
def test_same_source_plan_and_closed_command_contents():check.commands_checks()
def test_all_available_plans_members_and_selected_outcomes():check.availability_checks()
def test_same_institution_and_army_witnesses():check.witness_checks()
def test_unchanged_dependencies_and_preserved_full_description_domain():check.structure_checks()
